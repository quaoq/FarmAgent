from rsare.research_suite.families import RESEARCH_FAMILY_IDS, build_family_profile


def test_family_registry_has_all_10_profiles():
    assert len(RESEARCH_FAMILY_IDS) == 10
    for family_id in RESEARCH_FAMILY_IDS:
        profile = build_family_profile(family_id)
        assert profile.family_id == family_id
