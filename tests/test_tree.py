from silverturtle.tree import Node

TREE_DATA = {
    "tags": {
        "duplicate": {
            "pattern": "?|*",
            "comment": "The object is a duplicate. Can be a boolean flag or a reference to another object. Example: 'Copepod duplicate' or 'Copepod duplicate=object_id_001'.",
        },
        "badfocus": {"pattern": "?"},
        "part": {"pattern": "?|head|tail"},
        "like": {"pattern": "*"},
    },
    "comment": "The root node.",
    "children": {
        "Living": {
            "tags": {
                "egg": {"pattern": "?"},
                "adult": {"pattern": "?"},
                "fish": {"pattern": "?"},
            },
            "children": {
                "Animalia": {
                    "children": {
                        "Crustacea": {
                            "children": {
                                "Copepoda": {
                                    "tags": {
                                        "nauplius": {"pattern": "?|{1..6}"},
                                        "copepodit": {"pattern": "?|{1..5}"},
                                        "view": {
                                            "pattern": "lateral|dorsal-ventral|anterior-posterior"
                                        },
                                        "egg-bearing": {"pattern": "?"},
                                    },
                                    "children": {"Calanoida": {}},
                                },
                                "Pleuroncodes": {},
                            }
                        },
                        "Mollusca": {
                            "tags": {"veliger": {"pattern": "?"}},
                            "children": {"Cephalopoda": {}},
                        },
                        "Trichodesmium": {
                            "children": {
                                "Tuft": {},
                                "Puff": {"children": {"Radial": {}, "Non-Radial": {}}},
                            }
                        },
                        "Cnidaria": {
                            "tags": {"view": {"pattern": "lateral|oral-aboral"}}
                        },
                        "Rhizaria": {"children": {"Foraminifera": {}}},
                        "Appendicularia": {},
                        "Polychaeta": {},
                        "Ctenophora": {},
                        "Chaetognatha": {},
                        "Salpida": {},
                    }
                }
            },
        },
        "Detritus": {"children": {"Aggregate": {}, "Fiber": {}}},
        "Mix": {},
        "Artifact": {
            "aliases": ["artefact"],
            "children": {
                "Bubble": {"aliases": ["bubbles"]},
                "Scratch": {},
                "Seafloor": {},
            },
        },
        "Unknown": {},
    },
}


def test_from_dict():
    tree = Node.from_dict(TREE_DATA)
    print(tree)
