import spikeinterface.full as si

def whiten_rec_object(rec_object):
    job_kwargs = {"n_jobs": 20, "chunk_duration": "10s"}
    si.set_global_job_kwargs(**job_kwargs)

    print('Whitening recording object...')

    n_channels = rec_object.get_num_channels()
    fs = float(rec_object.get_sampling_frequency())

    target_bytes = 16 * 1024 * 1024 * 1024  # ~16 GiB
    bytes_per_sample = n_channels * 4  # float32
    max_samples = max(50_000, target_bytes // max(1, bytes_per_sample))

    chunk_duration = "1s"
    chunk_size = max(1, int(round(fs)))  # ~1 second in frames
    max_chunks_by_mem = int(max_samples // chunk_size)
    num_chunks_per_segment = max(1, min(10_000, max_chunks_by_mem))

    margin_frames = int(round(0.5 * fs))  # avoid edges/filter transients

    mode = "local"
    radius_um = 200.0

    rec_object = si.whiten(
        rec_object,
        dtype="float32",
        apply_mean=True,
        regularize=True,
        regularize_kwargs={"method": "LedoitWolf"},
        mode=mode,
        radius_um=radius_um,
        seed=0,
        method="full_random",
        chunk_duration=chunk_duration,
        num_chunks_per_segment=num_chunks_per_segment,
        margin_frames=margin_frames,
    )

    return rec_object
