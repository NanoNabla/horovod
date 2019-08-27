# Parameter knobs
HOROVOD_FUSION_THRESHOLD = 'HOROVOD_FUSION_THRESHOLD'
HOROVOD_CYCLE_TIME = 'HOROVOD_CYCLE_TIME'
HOROVOD_CACHE_CAPACITY = 'HOROVOD_CACHE_CAPACITY'
HOROVOD_HIERARCHICAL_ALLREDUCE = 'HOROVOD_HIERARCHICAL_ALLREDUCE'
HOROVOD_HIERARCHICAL_ALLGATHER = 'HOROVOD_HIERARCHICAL_ALLGATHER'

# Autotune knobs
HOROVOD_AUTOTUNE = 'HOROVOD_AUTOTUNE'
HOROVOD_AUTOTUNE_LOG = 'HOROVOD_AUTOTUNE_LOG'
HOROVOD_AUTOTUNE_WARMUP_SAMPLES = 'HOROVOD_AUTOTUNE_WARMUP_SAMPLES'
HOROVOD_AUTOTUNE_STEPS_PER_SAMPLE = 'HOROVOD_AUTOTUNE_STEPS_PER_SAMPLE'
HOROVOD_AUTOTUNE_BAYES_OPT_MAX_SAMPLES = 'HOROVOD_AUTOTUNE_BAYES_OPT_MAX_SAMPLES'
HOROVOD_AUTOTUNE_GAUSSIAN_PROCESS_NOISE = 'HOROVOD_AUTOTUNE_GAUSSIAN_PROCESS_NOISE'

# Timeline knobs
HOROVOD_TIMELINE = 'HOROVOD_TIMELINE'
HOROVOD_TIMELINE_MARK_CYCLES = 'HOROVOD_TIMELINE_MARK_CYCLES'

# Stall check knobs
HOROVOD_STALL_CHECK_DISABLE = 'HOROVOD_STALL_CHECK_DISABLE'
HOROVOD_STALL_CHECK_TIME_SECONDS = 'HOROVOD_STALL_CHECK_TIME_SECONDS'
HOROVOD_STALL_SHUTDOWN_TIME_SECONDS = 'HOROVOD_STALL_SHUTDOWN_TIME_SECONDS'

# Library options knobs
HOROVOD_MPI_THREADS_DISABLE = 'HOROVOD_MPI_THREADS_DISABLE'
HOROVOD_NUM_NCCL_STREAMS = 'HOROVOD_NUM_NCCL_STREAMS'
HOROVOD_MLSL_BGT_AFFINITY = 'HOROVOD_MLSL_BGT_AFFINITY'


def _set_arg_from_config(args, arg_base_name, override_args, config, arg_prefix=''):
    arg_name = arg_prefix + arg_base_name
    if arg_name in override_args:
        return

    value = config.get(arg_base_name)
    if value is not None:
        setattr(args, arg_name, value)


def set_args_from_config(args, config, override_args):
    # Controller
    controller = config.get('controller')
    if controller and not args.use_gloo and not args.use_mpi:
        if controller.lower() == 'gloo':
            args.use_gloo = True
        elif controller.lower() == 'mpi':
            args.use_mpi = True
        else:
            raise ValueError('No such controller supported: {}'.format(controller))

    # Params
    params = config.get('params')
    if params:
        _set_arg_from_config(args, 'fusion_threshold_mb', override_args, params)
        _set_arg_from_config(args, 'cycle_time_ms', override_args, params)
        _set_arg_from_config(args, 'cache_capacity', override_args, params)
        _set_arg_from_config(args, 'hierarchical_allreduce', override_args, params)
        _set_arg_from_config(args, 'hierarchical_allgather', override_args, params)

    # Autotune
    autotune = config.get('autotune')
    if autotune:
        args.autotune = autotune.get('enabled', False) if 'autotune' not in override_args else args.autotune
        _set_arg_from_config(args, 'log_file', override_args, autotune, arg_prefix='autotune_')
        _set_arg_from_config(args, 'warmup_samples', override_args, autotune, arg_prefix='autotune_')
        _set_arg_from_config(args, 'steps_per_sample', override_args, autotune, arg_prefix='autotune_')
        _set_arg_from_config(args, 'bayes_opt_max_samples', override_args, autotune, arg_prefix='autotune_')
        _set_arg_from_config(args, 'gaussian_process_noise', override_args, autotune, arg_prefix='autotune_')

    # Timeline
    timeline = config.get('timeline')
    if timeline:
        _set_arg_from_config(args, 'filename', override_args, timeline, arg_prefix='timeline_')
        _set_arg_from_config(args, 'mark_cycles', override_args, timeline, arg_prefix='timeline_')

    # Stall Check
    stall_check = config.get('stall_check')
    if stall_check:
        args.no_stall_check = not stall_check.get('enabled', True) \
            if 'no_stall_check' not in override_args else args.no_stall_check
        _set_arg_from_config(args, 'warning_time_seconds', override_args, stall_check, arg_prefix='stall_check_')
        _set_arg_from_config(args, 'shutdown_time_seconds', override_args, stall_check, arg_prefix='stall_check_')

    # Library Options
    library_options = config.get('library_options')
    if library_options:
        _set_arg_from_config(args, 'mpi_threads_disable', override_args, library_options)
        _set_arg_from_config(args, 'num_nccl_streams', override_args, library_options)
        _set_arg_from_config(args, 'mlsl_bgt_affinity', override_args, library_options)


def _validate_arg_nonnegative(args, arg_name):
    value = getattr(args, arg_name)
    if value < 0:
        raise ValueError('{}={} must be >= 0'.format(arg_name, value))


def validate_config_args(args):
    _validate_arg_nonnegative(args, 'fusion_threshold_mb')
    _validate_arg_nonnegative(args, 'cycle_time_ms')
    _validate_arg_nonnegative(args, 'cache_capacity')
    _validate_arg_nonnegative(args, 'autotune_warmup_samples')
    _validate_arg_nonnegative(args, 'autotune_steps_per_sample')
    _validate_arg_nonnegative(args, 'autotune_bayes_opt_max_samples')

    if args.autotune_gaussian_process_noise < 0 or args.autotune_gaussian_process_noise > 1:
        raise ValueError('{}={} must be in [0, 1]'.format('autotune_gaussian_process_noise',
                                                          args.autotune_gaussian_process_noise))

    _validate_arg_nonnegative(args, 'stall_check_warning_time_seconds')
    _validate_arg_nonnegative(args, 'stall_check_shutdown_time_seconds')
    _validate_arg_nonnegative(args, 'num_nccl_streams')
    _validate_arg_nonnegative(args, 'mlsl_bgt_affinity')


def _add_arg_to_env(env, env_key, arg_value, transform_fn=None):
    if arg_value is not None:
        value = arg_value
        if transform_fn:
            value = transform_fn(value)
        env[env_key] = str(value)


def set_env_from_args(env, args):
    def identity(value):
        return 1 if value else 0

    # Params
    _add_arg_to_env(env, HOROVOD_FUSION_THRESHOLD, args.fusion_threshold_mb, lambda v: v * 1024 * 1024)
    _add_arg_to_env(env, HOROVOD_CYCLE_TIME, args.cycle_time_ms)
    _add_arg_to_env(env, HOROVOD_CACHE_CAPACITY, args.cache_capacity)
    _add_arg_to_env(env, HOROVOD_HIERARCHICAL_ALLREDUCE, args.hierarchical_allreduce, identity)
    _add_arg_to_env(env, HOROVOD_HIERARCHICAL_ALLGATHER, args.hierarchical_allgather, identity)

    # Autotune
    if args.autotune:
        _add_arg_to_env(env, HOROVOD_AUTOTUNE, args.autotune, identity)
        _add_arg_to_env(env, HOROVOD_AUTOTUNE_LOG, args.autotune_log_file)
        _add_arg_to_env(env, HOROVOD_AUTOTUNE_WARMUP_SAMPLES, args.autotune_warmup_samples)
        _add_arg_to_env(env, HOROVOD_AUTOTUNE_STEPS_PER_SAMPLE, args.autotune_steps_per_sample)
        _add_arg_to_env(env, HOROVOD_AUTOTUNE_BAYES_OPT_MAX_SAMPLES, args.autotune_bayes_opt_max_samples)
        _add_arg_to_env(env, HOROVOD_AUTOTUNE_GAUSSIAN_PROCESS_NOISE, args.autotune_gaussian_process_noise)

    # Timeline
    if args.timeline_filename:
        _add_arg_to_env(env, HOROVOD_TIMELINE, args.timeline_filename)
        _add_arg_to_env(env, HOROVOD_TIMELINE_MARK_CYCLES, args.timeline_mark_cycles, identity)

    # Stall Check
    _add_arg_to_env(env, HOROVOD_STALL_CHECK_DISABLE, args.no_stall_check, identity)
    _add_arg_to_env(env, HOROVOD_STALL_CHECK_TIME_SECONDS, args.stall_check_warning_time_seconds)
    _add_arg_to_env(env, HOROVOD_STALL_SHUTDOWN_TIME_SECONDS, args.stall_check_shutdown_time_seconds)

    # Library Options
    _add_arg_to_env(env, HOROVOD_MPI_THREADS_DISABLE, args.mpi_threads_disable, identity)
    _add_arg_to_env(env, HOROVOD_NUM_NCCL_STREAMS, args.num_nccl_streams)
    _add_arg_to_env(env, HOROVOD_MLSL_BGT_AFFINITY, args.mlsl_bgt_affinity)

    return env