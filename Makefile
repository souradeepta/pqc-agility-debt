.PHONY: all experiments test paper clean

DATA_DIR    = data
RESULTS_DIR = results
PAPER_DIR   = paper
PAPER       = paper10

all: experiments test paper

experiments:
	python3 -m src.experiments --data-dir $(DATA_DIR) --results-dir $(RESULTS_DIR)

test:
	python3 -m pytest tests/ -v

paper: experiments
	cd $(PAPER_DIR) && pdflatex $(PAPER).tex && bibtex $(PAPER) && \
	  pdflatex $(PAPER).tex && pdflatex $(PAPER).tex

clean:
	cd $(PAPER_DIR) && rm -f *.aux *.bbl *.blg *.log *.out *.toc
	rm -f $(RESULTS_DIR)/*.pdf
