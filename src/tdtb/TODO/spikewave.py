from pathlib import Path
import spikeinterface.full as si
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def spikewave():
    tdt_path = input("TDT block path: ").strip().strip("'").strip()
    tdt_path = Path(tdt_path)
    sort_path = tdt_path / "sort_object"
    qual_path = tdt_path / "qual_object"
    wave_path = tdt_path / "spike_wave.pdf"

    if wave_path.exists():
        wave_path.unlink()

    sort_obj = si.load(sort_path)
    qual_obj = si.load(qual_path)

    unit_ids = sort_obj.get_unit_ids()
    unit_ids = sorted(unit_ids)

    unit2chan = si.get_template_extremum_channel(qual_obj)

    with PdfPages(wave_path) as pdf: 
        for unit in unit_ids:
            chan = unit2chan[unit]
            fig, ax = plt.subplots()
            si.plot_unit_waveforms(
                qual_obj,
                unit_ids=[unit],
                channel_ids=[chan],
                ax=ax,
                same_axis=True,
                plot_legend=False
            )
            ax.set_title(f'Unit {unit} (Channel {chan + 1})')
            ax.set_xlabel("Time (ms)")
            ax.set_ylabel("Voltage (uV)")
            
            pdf.savefig(fig)
            plt.close(fig)