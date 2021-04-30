import pathlib, argparse, sys, os, logging

from abritamr.AmrSetup import Setupamr
from abritamr.version import __version__

"""
mdu_amr is designed to implement AMRFinder and parse the results compatible for MDU use. It may also be used for other purposes where the format of output is compatible

Input types:
1). Assemblies - for MDU purposes those generated by the MDU QC pipeline (shovill with spades)

"""


def run_pipeline(args):
    P = Setupamr(args)
    return P.run_amr()


# abstract out toml functions into a separate class


def set_parsers():
    parser = argparse.ArgumentParser(
        description="MDU AMR gene detection pipeline", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument(
        "--mduqc",
        "-m",
        action="store_true",
        help="Set if running on MDU QC data. If set please provide the MDU QC .csv as further input and an additional output suitable for lims input will be provided.",
    )
    parser.add_argument(
        "--qc",
        "-q",
        default="mdu_qc_checked.csv",
        help="Name of checked MDU QC file."
    )
    parser.add_argument(
        "--positive_control",
        "-p",
        action = "store_true",
        help= "If you would like to include positive control. If running for MDU this will be included by default"
    )
    parser.add_argument(
        "--contigs",
        "-c",
        default="",
        help="Tab-delimited file with sample ID as column 1 and path to assemblies as column 2 OR path to a contig file (used if only doing a single sample - should provide value for -pfx). ",
    )
    parser.add_argument(
        "--prefix",
        "-px",
        default="abritamr",
        help="If running on a single sample, please provide a prefix for output directory",
    )
    
    parser.add_argument(
        "--workdir",
        "-w",
        default=f"{pathlib.Path.cwd().absolute()}",
        help="Working directory, default is current directory",
    )
    parser.add_argument(
        "--resources",
        "-r",
        default=f"{pathlib.Path(__file__).parent }",
        help="Directory where templates are stored",
    )

    parser.add_argument(
        "--species",
        "-sp",
        default="",
        help="Set if you would like to use point mutations, please provide a valid species.",
        choices= ['Acinetobacter_baumannii', "Campylobacter", "Enterococcus_faecalis", "Enterococcus_faecium", "Escherichia", "Klebsiella", "Salmonella", "Staphylococcus_aureus", "Staphylococcus_pseudintermedius", "Streptococcus_agalactiae", "Streptococcus_pneumoniae", "Streptococcus_pyogenes", "Vibrio_cholerae"]
    )
    parser.add_argument(
        "--jobs", "-j", default=16, help="Number of AMR finder jobs to run in parallel."
    )
    parser.add_argument(
        "--keep",
        "-k",
        action="store_true",
        help="If you would like to keep intermediate files and snakemake log. Default is to remove",
    )
    parser.set_defaults(func=run_pipeline)
    args = parser.parse_args()
    return args


def main():
    """
    run pipeline
    """

    args = set_parsers()
    if vars(args) == {}:
        parser.print_help(sys.stderr)
    else:
        # print(logging.__file__)
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        # # create file handler which logs even debug messages
        # # create file handler which logs even debug messages
        fh = logging.FileHandler('abritamr.log')
        fh.setLevel(logging.INFO)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('[%(levelname)s:%(asctime)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(ch)
        logger.addHandler(fh)
        logger.info(f"Starting AMR detection using {' '.join(sys.argv)}")
        args.func(args)
    

if __name__ == "__main__":
    main()
