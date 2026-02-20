from probeinterface import generate_linear_probe, get_probe, Probe
import numpy as np
import spikeinterface.full as si

def extract_rec_object(probe_data):
    probe_type = probe_data['probe_type']
    chan_count = probe_data['chan_count']
    bin_path = probe_data['bin_path']
    sampling_freq = probe_data['sampling_freq']

    if probe_type == 'SP':
        probe = generate_linear_probe(
            num_elec=chan_count,
            ypitch=100,
            contact_shapes="circle",
        )
    elif probe_type == 'NP':
        channel_ids = probe_data['channel_ids']
        # NP 1.0 NHP long linear (45mm shank): NP1032
        # NP 1.0 rodent standard: NP1000
        full_probe = get_probe('imec', 'NP1000')
        positions = full_probe.contact_positions[channel_ids]
        probe = Probe()
        probe.set_contacts(
            positions=positions,
            shapes='square',
            shape_params={'width': 12},
        )
        probe.create_auto_shape()

    print('Extracting recording object...')

    probe.set_device_channel_indices(np.arange(chan_count))
    rec_object = si.BinaryRecordingExtractor(
        file_paths=bin_path,
        sampling_frequency=sampling_freq,
        num_channels=chan_count,
        dtype='float32'
    )
    rec_object.set_probe(probe, in_place=True)

    return rec_object
