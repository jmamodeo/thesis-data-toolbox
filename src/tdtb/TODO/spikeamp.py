from pathlib import Path
import spikeinterface.full as si
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def spikeamp():
    tdt_path = input("TDT block path: ").strip().strip("'").strip()
    tdt_path = Path(tdt_path)
    sort_path = tdt_path / "sort_object"
    qual_path = tdt_path / "qual_object"
    amp_path = tdt_path / "spike_amp.pdf"

    if amp_path.exists():
        amp_path.unlink()

    sort_obj = si.load(sort_path)
    qual_obj = si.load(qual_path)

    unit_ids = sort_obj.get_unit_ids()
    unit_ids = sorted(unit_ids)

    unit2chan = si.get_template_extremum_channel(qual_obj)

    with PdfPages(amp_path) as pdf: 
        for unit in unit_ids:
            chan = unit2chan[unit]
            fig, ax = plt.subplots()
            si.plot_amplitudes(
                qual_obj,
                unit_ids=[unit],
                ax=ax,
                plot_legend=False
            )
            ax.set_title(f'Unit {unit} (Channel {chan + 1})')
            
            plt.tight_layout()
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)