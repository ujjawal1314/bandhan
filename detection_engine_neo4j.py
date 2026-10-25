"""
Compatibility wrapper for the borrower-health engine.

The old project exposed a Neo4j-specific detector entry point. Bandhan now
uses a borrower-health scoring engine that does not require Neo4j for the MVP,
but this wrapper keeps the import path stable for the rest of the codebase.
"""

from detection_engine import SatarkSetuDetector


class SatarkSetuDetectorNeo4j(SatarkSetuDetector):
    def __init__(self, borrower_df, txn_df, regional_df=None, use_neo4j: bool = True):
        self.use_neo4j = use_neo4j
        super().__init__(borrower_df, txn_df, regional_df=regional_df)
