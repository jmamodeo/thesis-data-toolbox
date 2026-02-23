from tdt import read_block
import numpy as np
from pathlib import Path
import spikeinterface.full as si
import shutil
import io
from contextlib import redirect_stderr, redirect_stdout

from tdtb.functions.extract_rec_object import extract_rec_object
from tdtb.functions.whiten_rec_object import whiten_rec_object
from tdtb.functions.get_chan_traces import get_chan_traces

def read_block_silent(*args, **kwargs):
    """Wrapper for read_block that suppresses stderr and stdout."""
    with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):

        return read_block(*args, **kwargs)

def get_tdt_headers(tdt_path):
    tdt_headers = read_block_silent(tdt_path, headers=1)
    for store_name in tdt_headers.stores.keys():
        store = tdt_headers.stores[store_name]
        if hasattr(store, "chan"):
            store.chan = store.chan.astype(np.int32)

    return tdt_headers

def get_rec_duration(tdt_path, tdt_headers):
    streams_block = read_block_silent(tdt_path, headers=tdt_headers, t1=0, t2=1)
    try:
        duration = int(streams_block.info['duration'].total_seconds())
    except:
        print('Could not find recording duration')
        print('Calculating duration from snips...')
        snips_block = read_block_silent(tdt_path, headers=tdt_headers, evtype=['snips'])
        snip_keys = list(snips_block.snips.keys())
        print('Available snip keys: ', snip_keys)
        snip_key = input('Enter snip key to use: ').strip()
        snips_data = snips_block.snips[snip_key]
        duration = int(snips_data.ts[-1][0])
    print('Recording duration (s): ', duration)

    return duration

def get_stream_name(tdt_path, tdt_headers):
    streams_block = read_block_silent(
        tdt_path, 
        headers=tdt_headers, 
        t1=0, t2=1, 
        evtype=['streams']
    )
    stream_names = list(streams_block.streams.keys())
    print('Available stream names: ', stream_names)
    stream_name = input('Enter stream name to use: ').strip()
    
    return stream_name

def get_sampling_freq(tdt_path, tdt_headers, stream_name):
    streams_block = read_block_silent(
        tdt_path, 
        headers=tdt_headers, 
        t1=0, t2=1, 
        evtype=['streams']
    )
    frequency = float(streams_block.streams[stream_name].fs)
    print('Sampling frequency: ', frequency)

    return frequency

def get_channel_count(tdt_path, tdt_headers, stream_name):
    streams_block = read_block_silent(
        tdt_path, 
        headers=tdt_headers, 
        t1=0, t2=1, 
        evtype=['streams']
    )
    chan_count = int(streams_block.streams[stream_name].data.shape[0])
    print('Number of channels: ', chan_count)

    return chan_count

def get_channel_ids(tdt_path, tdt_headers, stream_name):
    streams_block = read_block_silent(
        tdt_path, 
        headers=tdt_headers, 
        t1=0, t2=1, 
        evtype=['streams']
    )
    chan_ids = streams_block.streams[stream_name].channels

    return chan_ids

def get_block_chunks(rec_duration, chunk_size):
    chunks = []
    for chunk_start in range(0, rec_duration, chunk_size):
        chunk_end = min(chunk_start + chunk_size, rec_duration)
        chunks.append((chunk_start, chunk_end))

    return chunks

def write_binary_file(
        tdt_path,
        tdt_headers, 
        bin_path, 
        stream_name, 
        block_chunks, 
        sampling_freq, 
        chan_count
    ):
    print('Writing block chunks to binary file...')
    with open(bin_path, 'wb') as f:
        in_gap = False
        for chunk_start, chunk_end in block_chunks:
            sample_count = int(round((chunk_end - chunk_start) * sampling_freq))
            pos_val = 0.0
            neg_val = 0.0
            chunk_block = read_block_silent(
                tdt_path,
                headers=tdt_headers, 
                store=stream_name,
                evtype=['streams'],
                t1=chunk_start, 
                t2=chunk_end
            )
            chunk_data = chunk_block.streams[stream_name].data.T
            if chunk_data.size == 0:
                in_gap = True
                chunk_data = np.zeros((sample_count, chan_count), dtype=np.float32)
            elif chunk_data.shape[0] < sample_count:
                pad = sample_count - chunk_data.shape[0]
                if in_gap:
                    # Leaving gap
                    in_gap = False
                    chunk_data = np.pad(chunk_data, ((pad, 0), (0, 0)), mode='constant', constant_values=0.0)
                else:
                    # Entering gap
                    in_gap = True
                    chunk_data = np.pad(chunk_data, ((0, pad), (0, 0)), mode='constant', constant_values=0.0)
                finite_mask = np.isfinite(chunk_data)
                if finite_mask.any():
                    pos_val = np.nanmax(chunk_data)
                    neg_val = np.nanmin(chunk_data)
            else:
                in_gap = False
                finite_mask = np.isfinite(chunk_data)
                if finite_mask.any():
                    pos_val = np.nanmax(chunk_data)
                    neg_val = np.nanmin(chunk_data)

            clean_chunk = np.nan_to_num(chunk_data, nan=0.0, posinf=pos_val, neginf=neg_val)
            chunk_binary = clean_chunk.astype(np.float32).tobytes()
            f.write(chunk_binary)
            print(f"Wrote chunk {chunk_start}-{chunk_end} ({chunk_data.shape[0]} samples)")

def procrec():
    tdt_path = input("TDT block path: ").strip().strip("'").strip()
    analysis_path = Path(tdt_path) / 'analysis'
    bin_path = analysis_path / "raw_stream.bin"
    raw_path = analysis_path / "raw_rec"
    filtered_path = analysis_path / "filtered_rec"
    whitened_path = analysis_path / "whitened_rec"

    if bin_path.exists():
        bin_path.unlink()
    if raw_path.exists():
        shutil.rmtree(raw_path)
    raw_path.mkdir()
    if filtered_path.exists():
        shutil.rmtree(filtered_path)
    filtered_path.mkdir()
    if whitened_path.exists():
        shutil.rmtree(whitened_path)
    whitened_path.mkdir()

    tdt_headers = get_tdt_headers(tdt_path)
    rec_duration = get_rec_duration(tdt_path, tdt_headers)
    stream_name = get_stream_name(tdt_path, tdt_headers)

    probe_types = {'SP': 500, 'NP': 50}
    print('Available probe types:', f'{list(probe_types.keys())}')
    probe_type = input('Enter probe type to use: ').strip()

    chunk_size = probe_types[probe_type]

    sampling_freq = get_sampling_freq(tdt_path, tdt_headers, stream_name)
    chan_count = get_channel_count(tdt_path, tdt_headers, stream_name)
    block_chunks = get_block_chunks(rec_duration, chunk_size)

    write_binary_file(
        tdt_path,
        tdt_headers, 
        bin_path, 
        stream_name, 
        block_chunks, 
        sampling_freq, 
        chan_count
    )

    job_kwargs = {"n_jobs": 20, "chunk_duration": "10s"}
    si.set_global_job_kwargs(**job_kwargs)

    raw_rec_path = raw_path / "rec_object"
    probe_data = {
        'probe_type': probe_type,
        'bin_path': bin_path,
        'sampling_freq': sampling_freq,
        'chan_count': chan_count,
    }

    if probe_type == 'NP':
        channel_ids = get_channel_ids(tdt_path, tdt_headers, stream_name)
        probe_data['channel_ids'] = channel_ids

    rec_object = extract_rec_object(probe_data)
    rec_object.save(folder=raw_rec_path)
    get_chan_traces(raw_path)
    
    filtered_rec_path = filtered_path / "rec_object"
    try:
        rec_object = si.center(rec_object)
        rec_object = si.bandpass_filter(
            rec_object, 
            freq_min=300, 
            freq_max=6000,
        )
    except ValueError as e:
        print(e)
        print('Frequency too low for filtering. Skipping...')
    rec_object.save(folder=filtered_rec_path)
    get_chan_traces(filtered_path)

    whitened_rec_path = whitened_path / "rec_object"
    rec_object = whiten_rec_object(rec_object)
    rec_object.save(folder=whitened_rec_path)
    get_chan_traces(whitened_path)
    