"variants_lister.py - Get variants using the CIVIC API"

import argparse
from flask import Flask, render_template, url_for
import json
import requests
requests.packages.urllib3.disable_warnings()

import civic_api_client
import utils
from variants_lister import VariantsLister, VariantDetails

class EvidenceItems:
    variant_id = ""
    doid = ""
    variant_civic_url = ""

    def __init__(self, variant_id, doid, variant_civic_url):
        "Constructor"
        self.variant_id = variant_id
        self.doid = doid
        self.variant_civic_url = variant_civic_url

class EvidenceItemsLister:
    """Represent the evidence-items in CIVIC"""
    queried_doids = {}
    invalid_eis = []
    def __init__(self, args):
        "Constructor"
        self.args = args
    def parse_args(self):
        "Parse command-line arguments"
        parser = argparse.ArgumentParser(description="civic-api-client version {}".format(civic_api_client.__version__),
            usage = "civic-api-client evidence-items-list",
            formatter_class = argparse.RawTextHelpFormatter,
        )
        parser.add_argument("--doid",
            action='store_true',
            help = "Print evidence-items with improper DOID.(not defined"\
                    "on disease-ontology.org)"
        )
        parser.add_argument("--max-gene-count",
            help = "Maximum number of genes to query from CIVIC [100,000]",
            type = int,
            default = 100000
        )
        parser.add_argument("--web",
            action='store_true',
            help = "Publish evidence-items to a webpage."
        )
        args = parser.parse_args(self.args)
        print "Max number of genes to query is ",args.max_gene_count
        self.args = args

    def check_doid(self, variant_id, variant_detail, evidence_items):
        "Check if DOID is valid, if not add to list of invalids"
        for evidence_item in evidence_items:
            doid = evidence_item['disease']['doid']
            #Query each DOID once
            if doid not in self.queried_doids:
                self.queried_doids[doid] = 1
                url = utils.disease_ontology_api_url() + \
                        "metadata/DOID:" + str(doid)
                r = requests.get(url, verify = False)
                try:
                    r.raise_for_status()
                except requests.exceptions.HTTPError:
                    ei1 = EvidenceItems(variant_id, doid, \
                                        VariantDetails.define_civic_url(variant_detail))
                    self.invalid_eis.append(ei1)

    def display_invalid_eis(self):
        "Display the invalid DOIDs"
        if self.args.web:
            self.display_invalid_web()
        else:
            print "Printing invalid DOIDs"
            for ei1 in self.invalid_eis:
                print ei1.doid + "\t" + ei1.variant_id + "\t" + ei1.variant_civic_url + "\n"

    def display_invalid_eis_web(self):
        "Publish to web page"
        app = Flask("civic_api_client")
        @app.route("/")
        def template_test():
                return render_template('evidence-items.html', \
                        invalid_eis = self.invalid_eis)
        app.run(debug=True)

    def create_invalid_eis_list(self):
        "Create the list of invalid evidence items"
        vl1 = VariantsLister(self.args)
        vl1.get_civic_genes()
        variant_ids = vl1.get_variant_ids()
        for variant_id in variant_ids:
            variant_detail = vl1.get_variant_details(variant_id)
            if "evidence_items" in variant_detail:
                evidence_items = variant_detail['evidence_items']
                if self.args.doid:
                    #If not valid, add to list of invalids
                    self.check_doid(variant_id, variant_detail, evidence_items)

    def get_invalid_eis(self):
        "Return the list of invalid DOIDs"
        return self.invalid_eis

    def main(self):
        "Execution starts here"
        self.parse_args()
        self.create_invalid_eiss_list()
        self.display_invalid_eis()
