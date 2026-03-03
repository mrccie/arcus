/* SPDX-License-Identifier: BSD-2-Clause */
/*
 * object_detect_emit_udp_stage.cpp
 *
 * Consumes object detection results (object_detect.results), selects a single target per frame,
 * and emits one JSON message per frame over UDP via an async writer thread.
 *
 * Notes:
 *  - The writer loop is best-effort: send failures do not backpressure Process()
 *  - If UDP init fails, the thread drains/discards so the queue cannot grow unbounded
 *  - The try/catch around Get() is defensive. If Get() in the build does not throw 
 *    and instead leaves the vector empty, this still behaves correctly
 * 
 * Guarantees:
 *  - Process() never blocks on I/O
 *  - bounded queue, drop-oldest
 */

#include "core/rpicam_app.hpp"
#include "post_processing_stages/post_processing_stage.hpp"
#include "post_processing_stages/object_detect.hpp"

#include <algorithm>
#include <atomic>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <deque>
#include <mutex>
#include <condition_variable>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

// UDP / sockets
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

class ObjectDetectEmitUDPStage : public PostProcessingStage
{
public:
        ObjectDetectEmitUDPStage(RPiCamApp *app) : PostProcessingStage(app) {}

        char const *Name() const override { return NAME; }

        void Read(boost::property_tree::ptree const &params) override
        {
                // Selection
                label_ = params.get<std::string>("label", label_);

                // Coordinate-space descriptor for bbox we emit.
                // Default 640x640 matches your hailo_yolov8_inference.json lores size.
                frame_w_override_ = params.get<int>("frame_w", frame_w_override_);
                frame_h_override_ = params.get<int>("frame_h", frame_h_override_);

                // Queue
                queue_depth_ = params.get<size_t>("queue_depth", queue_depth_);
                if (queue_depth_ < 1)
                        queue_depth_ = 1;

                // Drop-report telemetry
                report_every_n_ = params.get<size_t>("report_every_n", report_every_n_);
                if (report_every_n_ < 1)
                        report_every_n_ = 1;

                // UDP
                udp_ip_ = params.get<std::string>("ip", udp_ip_);
                udp_port_ = params.get<uint16_t>("port", udp_port_);
        }

        void Configure() override
        {
                // No heavy work here; socket init in Start() so failures are visible per-run.
        }

        void Start() override
        {
                // Determine the coordinate-space of Detection::box.
                // For Hailo YOLO in this pipeline, boxes are in the main/video coordinate system.
                StreamInfo main_info;
                auto *main = app_->GetMainStream();
                if (main)
                        main_info = app_->GetStreamInfo(main);

                if (main_info.width > 0 && main_info.height > 0)
                {
                        frame_w_ = static_cast<int>(main_info.width);
                        frame_h_ = static_cast<int>(main_info.height);
                }
                else
                {
                        // Fallback: try lores if main isn't available for some reason
                        StreamInfo lores_info;
                        auto *lores = app_->LoresStream(&lores_info);
                        if (lores && lores_info.width > 0 && lores_info.height > 0)
                        {
                                // Defaults from runtime (lores stream)
                                frame_w_ = static_cast<int>(lores_info.width);
                                frame_h_ = static_cast<int>(lores_info.height);
                        }
                }

                // Optional explicit override from JSON, if provided (>0)
                if (frame_w_override_ > 0) frame_w_ = frame_w_override_;
                if (frame_h_override_ > 0) frame_h_ = frame_h_override_;

                // Init UDP socket
                sockfd_ = ::socket(AF_INET, SOCK_DGRAM, 0);
                if (sockfd_ < 0)
                {
                        // If socket creation fails, we disable UDP but keep pipeline running.
                        sockfd_ = -1;
                        udp_enabled_ = false;
                }
                else
                {
                        std::memset(&destaddr_, 0, sizeof(destaddr_));
                        destaddr_.sin_family = AF_INET;
                        destaddr_.sin_port = htons(udp_port_);

                        if (::inet_pton(AF_INET, udp_ip_.c_str(), &destaddr_.sin_addr) <= 0)
                        {
                                ::close(sockfd_);
                                sockfd_ = -1;
                                udp_enabled_ = false;
                        }
                        else
                        {
                                udp_enabled_ = true;
                        }
                }

                // Start writer thread regardless; if UDP is disabled it will just drain/discard.
                stop_ = false;
                writer_ = std::thread(&ObjectDetectEmitUDPStage::WriterLoop, this);
        }

        bool Process(CompletedRequestPtr &completed_request) override
        {
                const uint64_t seq = seq_++;

                // hailo_yolo_inference only sets metadata when objects.size() > 0; missing key == "not found".
                std::vector<Detection> detections;
                bool have_results = false;
                try
                {
                        completed_request->post_process_metadata.Get("object_detect.results", detections);
                        have_results = true;
                }
                catch (...)
                {
                        have_results = false;
                }

                // Select best match: largest bbox area; tie-break by confidence.
                const Detection *best = nullptr;
                int64_t best_area = -1;
                float best_conf = -1.0f;

                if (have_results && !detections.empty())
                {
                        for (auto const &d : detections)
                        {
                                if (d.name != label_)
                                        continue;

                                const int w = std::max(0, static_cast<int>(d.box.width));
                                const int h = std::max(0, static_cast<int>(d.box.height));
                                const int64_t area = static_cast<int64_t>(w) * static_cast<int64_t>(h);

                                if (area > best_area || (area == best_area && d.confidence > best_conf))
                                {
                                        best = &d;
                                        best_area = area;
                                        best_conf = d.confidence;
                                }
                        }
                }

                std::string json = BuildJson(seq, best);
                Enqueue(std::move(json));

                return false; // never drop frames
        }

        void Stop() override
        {
                {
                        std::lock_guard<std::mutex> lk(mutex_);
                        stop_ = true;
                }
                cv_.notify_one();

                if (writer_.joinable())
                        writer_.join();
        }

        void Teardown() override
        {
                if (sockfd_ != -1)
                {
                        ::close(sockfd_);
                        sockfd_ = -1;
                }
        }

        ~ObjectDetectEmitUDPStage() override
        {
                // Be defensive in case Stop/Teardown aren't called in some path.
                try { Stop(); } catch (...) {}
                try { Teardown(); } catch (...) {}
        }

private:
        static constexpr const char *NAME = "object_detect_emit_udp";

        // Config
        std::string label_ = "person";
        int frame_w_ = 0;
        int frame_h_ = 0;

        // Optional overrides from JSON (0 means "not specified")
        int frame_w_override_ = 0;
        int frame_h_override_ = 0;

        size_t queue_depth_ = 8;
        size_t report_every_n_ = 30;
        std::string udp_ip_ = "127.0.0.1";
        uint16_t udp_port_ = 12347;

        // Queue + sync
        std::mutex mutex_;
        std::condition_variable cv_;
        std::deque<std::string> queue_;
        std::atomic<uint64_t> seq_{0};
        std::atomic<uint64_t> dropped_{0};

        // Writer thread control
        std::thread writer_;
        bool stop_ = false;

        // UDP
        int sockfd_ = -1;
        sockaddr_in destaddr_{};
        bool udp_enabled_ = false;

        void Enqueue(std::string &&msg)
        {
                {
                        std::lock_guard<std::mutex> lk(mutex_);
                        // Drop-oldest
                        while (queue_.size() >= queue_depth_)
                        {
                                queue_.pop_front();
                                dropped_++;
                        }
                        queue_.push_back(std::move(msg));
                }
                cv_.notify_one();
        }

        void WriterLoop()
        {
                for (;;)
                {
                        std::string msg;

                        {
                                std::unique_lock<std::mutex> lk(mutex_);
                                cv_.wait(lk, [&] { return stop_ || !queue_.empty(); });

                                if (stop_ && queue_.empty())
                                        break;

                                // Pop oldest (we keep newest by drop-oldest on enqueue)
                                msg = std::move(queue_.front());
                                queue_.pop_front();
                        }

                        // If UDP is not available, discard silently.
                        if (!udp_enabled_ || sockfd_ == -1)
                                continue;

                        // Send one datagram per frame message.
                        const ssize_t sent = ::sendto(sockfd_,
                                                      msg.data(),
                                                      msg.size(),
                                                      0,
                                                      reinterpret_cast<const sockaddr *>(&destaddr_),
                                                      sizeof(destaddr_));
                        (void)sent; // best-effort; drops are acceptable
                }
        }

        std::string BuildJson(uint64_t seq, const Detection *d) const
        {
                std::ostringstream os;
                os.setf(std::ios::fixed);
                os.precision(6);

                os << "{"
                   << "\"seq\":" << seq << ","
                   << "\"label\":\"" << EscapeJson(label_) << "\","
                   << "\"frame_w\":" << frame_w_ << ","
                   << "\"frame_h\":" << frame_h_ << ",";


                const bool report_drop = (report_every_n_ > 0) && (seq % report_every_n_ == 0);
                if (report_drop)
                        os << "\"dropped\":" << dropped_.load() << ",";

                if (!d)
                {
                        os << "\"found\":false"
                           << "}";
                        return os.str();
                }

                os << "\"found\":true,"
                   << "\"x\":" << d->box.x << ","
                   << "\"y\":" << d->box.y << ","
                   << "\"w\":" << d->box.width << ","
                   << "\"h\":" << d->box.height << ","
                   << "\"confidence\":" << d->confidence
                   << "}";

                return os.str();
        }

        static std::string EscapeJson(const std::string &s)
        {
                std::string out;
                out.reserve(s.size() + 8);
                for (char c : s)
                {
                        switch (c)
                        {
                        case '\\': out += "\\\\"; break;
                        case '"':  out += "\\\""; break;
                        case '\b': out += "\\b"; break;
                        case '\f': out += "\\f"; break;
                        case '\n': out += "\\n"; break;
                        case '\r': out += "\\r"; break;
                        case '\t': out += "\\t"; break;
                        default:
                                if (static_cast<unsigned char>(c) < 0x20)
                                {
                                        char buf[7];
                                        std::snprintf(buf, sizeof(buf), "\\u%04x", c & 0xff);
                                        out += buf;
                                }
                                else
                                {
                                        out += c;
                                }
                                break;
                        }
                }
                return out;
        }
};

static PostProcessingStage *Create(RPiCamApp *app)
{
        return new ObjectDetectEmitUDPStage(app);
}

static RegisterStage reg("object_detect_emit_udp", &Create);
