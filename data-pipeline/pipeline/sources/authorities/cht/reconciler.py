from pipeline.process.base.reconciler import LmdbReconciler

# Types that CHT can authoritatively classify.  We intentionally exclude
# Language, Currency, and MeasurementUnit — those are better covered by AAT.
CHT_RECONCILE_TYPES = {"Type", "Material", "Concept"}

CHT_NAMESPACE = "https://data.cultureelerfgoed.nl/term/id/cht/"


class ChtReconciler(LmdbReconciler):
    """Reconcile Type/Material/Concept records against the Dutch CHT thesaurus.

    Runs before AatReconciler (lower merge_order = higher priority) so that
    Dutch CHE objects preferentially get CHT URIs, which often carry an
    exactMatch to AAT via the equivalent field.
    """

    def extract_names(self, rec: dict) -> dict:
        """Extract Dutch prefLabel and altLabels as reconciliation candidates.

        Returns a dict of {lowercase_label: priority} where lower priority
        numbers are preferred.  Priority 1 = prefLabel, 2 = altLabel.
        """
        vals: dict[str, int] = {}

        # prefLabel stored directly on the record by the harvester
        pref = rec.get("prefLabel", "") or rec.get("_label", "")
        if pref:
            vals[self.clean_names(pref)] = 1

        # altLabels — stored in identified_by by the mapper after transform
        for nm in rec.get("identified_by", []):
            content = nm.get("content", "")
            if not content:
                continue
            cxns = [cx.get("id", "") for cx in nm.get("classified_as", [])]
            # PrimaryName class id used by vocab
            is_primary = any("300404670" in cx for cx in cxns)
            if not is_primary and content:
                vals[self.clean_names(content)] = 2

        return vals

    def should_reconcile(self, rec: dict, reconcileType: str = "all") -> bool:
        if not LmdbReconciler.should_reconcile(self, rec, reconcileType):
            return False

        data = rec.get("data", rec)

        if data.get("type") not in CHT_RECONCILE_TYPES:
            return False

        # Skip if we already assigned a CHT equivalent in a prior pass
        eqids = [
            x["id"]
            for x in data.get("equivalent", [])
            if CHT_NAMESPACE in x.get("id", "")
        ]
        return not eqids
