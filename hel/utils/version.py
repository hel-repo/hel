# -*- coding: utf-8 -*-
import semantic_version as semver


def latest_version(package):
    versions = (semver.Version(x) for x in package['versions'])
    return semver.Spec('*').select(versions)
