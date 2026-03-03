threads_dep = dependency('threads')

emit_postproc_src = files([
  '../hailo/object_detect_emit_udp_stage.cpp',
])

emit_postproc_lib = shared_module('emit-postproc', emit_postproc_src,
  include_directories : '../..',
  dependencies : [libcamera_dep, threads_dep],
  cpp_args : cpp_arguments,
  install : true,
  install_dir : posproc_libdir,
  name_prefix : '',
)
