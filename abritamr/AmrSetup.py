import pathlib, pandas, datetime, getpass, logging, jinja2, re, subprocess, os


"""
A class for setting up mdu-amr
"""


class Setupamr(object):
    def __init__(self, args):
        # some variables to be use

        self.workdir = pathlib.Path(args.workdir)
        self.resources = pathlib.Path(args.resources)
        self.jobs = args.jobs
        self.mduqc = args.mduqc
        self.drugs = pathlib.Path(args.drug_classes)
        self.contigs = args.contigs
        self.amrfinder_output = args.amrfinder_output
        self.from_contigs = True
        self.keep = args.keep

    def file_present(self, name):
        """
        check file is present
        """
        if name == "":
            return False
        elif pathlib.Path(name).exists():
            return True
        else:
            return False

    def check_input_exists(self):
        """
        check that all files required are present. 
        If both contigs and amrfinder are absent (or both present) provide warning and exit.
        If mduqc is true ensure that the mdu_qc_checked file is present
        """

        if self.mduqc and not self.file_present("mdu_qc_checked.csv"):
            logging.warning(
                "You appear to be trying to run mdu-amr in the context of mdu-qc, but the mdu_qc_checked.csv file is not present. Please check your settings and try again."
            )
            raise SystemExit

        if (
            not self.file_present(self.contigs)
            and not self.file_present(self.amrfinder_output)
            and not self.mduqc
        ):
            logging.warning(
                "You have not provided a valid path to any input files. Please provide a file containing paths to assemblies or amrfinder outputs."
            )
            raise SystemExit
        elif self.file_present(self.contigs) and self.file_present(
            self.amrfinder_output
        ):
            logging.warning(
                "You seem to have provided both assemblies and amrfinder results. Only one is required. Please check your setting and try again."
            )
            raise SystemExit

        if self.file_present(self.contigs):
            self.from_contigs = True
        elif self.file_present(self.amrfinder_output):
            self.from_contigs = False

        return True

    def make_links(self, first_column, second_column):
        """
        link files
        """
        target_name = "contigs.fa" if self.from_contigs else f"{first_column}.out"
        isolate_dir = self.workdir / f"{first_column}"
        if not isolate_dir.exists():
            isolate_dir.mkdir()

        target = isolate_dir / target_name
        if not target.exists():
            target.symlink_to(pathlib.Path(f"{second_column}"))

    def check_input_tab(self, tab):

        if tab.shape[1] == 2:
            return True
        else:
            logging.warning(
                "Your input file should be a tab delimited file with two columns. Please check your input and try again."
            )
            raise SystemExit

    def link_input_files(self):
        """
        Ensure that the files (either contigs or amrfinder output) exist and generate structure for links
        """
        input_file = (
            pathlib.Path(self.contigs)
            if self.from_contigs
            else pathlib.Path(self.amrfinder_output)
        )
        tab = pandas.read_csv(input_files, engine="python", header=None)
        self.check_input_tab(tab)
        for row in tab.iterrows():
            if self.file_present(row[1][1]):
                self.make_links(first_column=row[1][0], second_column=row[1][0])
        return list(tab[0])

    def generate_workflow_files(self):
        # varaiables for config.yaml
        script_path = self.resources / "utils"
        amrfinder = "" if self.from_contigs else "run_amrfinder"
        mduqc = "mduqc" if self.mduqc else ""

        config_source = self.resources / "templates" / "config.yaml"
        config_template = jinja2.Template(config_source).read_text()
        config_target = self.workdir / "config.yaml"
        config_target.write_text(
            config_template.render(
                script_path=script_path, amrfinder=amrfinder, mduqc=mduqc
            )
        )

        # variables for snakemake
        finaloutput = (
            f"MMS118.xlsx"
            if self.mduqc
            else f"summary_matches.csv, summary_partials.csv"
        )
        workdir = f"'{self.workdir}''"

        snk_source = self.resources / "templates" / "Snakefile"
        snk_template = jinja2.Template(snk_source).read_text()
        snk_target = self.workdir / "Snakefile"
        snk_target.write_text(
            snk_template.render(finaloutput=finaloutput, workdir=workdir)
        )

        logging.info(f"Written Snakefile and config.yaml to {self.workdir}")

    def run_snakemake(self):

        logging.info("Running pipeline. This may take some time.")
        cmd = f"snakemake -s Snakefile -j {self.jobs} 2>&1 | tee -a job.log"
        wkfl = subprocess.run(cmd, shell=True, capture_output=True)

        if wkfl.returncode == 0:
            return True
        else:
            return False

    def clean(self):

        logs = self.workdir / ".snakemake" / "log"
        if logs.exists():
            rmlog = subprocess.run(f"rm -rf {logs}", shell=True, capture_output=True)
            if rmlog.returncode == 0:
                logging.info("Removed old log files")
        conda = self.workdir / ".snakemake" / "conda"
        if conda.exists():
            cleanconda = subprocess.run(
                f"snakemake --cleanup-conda", shell=True, capture_output=True
            )
            if cleanconda.returncode == 0:
                logging.info("Cleaned unused conda environments")

    def run_amr(self):

        # setup the pipeline
        self.check_input_exists()
        self.check_input_tab()
        self.link_input_files()
        # write snakefile
        self.generate_workflow_files()
        # run snakefile
        if self.run_snakemake():
            logging.info(f"Pipeline completed")
            if not self.keep:
                logging.info(f"Cleaning up the working directory.")
                self.clean()
            logging.info("Thank you and come again!")
