# Compatibility Cleanup Plan

This document is planning-only.

## Compatibility areas

### `guards.py`

Status:
- remove later

Reason:
- legacy compatibility path
- overlaps with newer module responsibilities

### legacy reporting path

Status:
- deprecate

Reason:
- mixed old and newer reporting behavior
- should stop growing before later cleanup

### config-dependent state handling

Status:
- refactor

Reason:
- older configuration coupling still remains
- should move to a cleaner input shape later

### config-dependent reporting handling

Status:
- refactor

Reason:
- reporting still carries older configuration dependence
- should move to a cleaner boundary later

### config bridge behavior in runtime settings

Status:
- keep

Reason:
- still serves a transitional purpose
- not ready for removal

### legacy entrypoint remnants

Status:
- deprecate

Reason:
- older flow assumptions still appear around entrypoint responsibility
- should be reduced before any later removal

## Cleanup order

1. deprecate legacy reporting path
2. deprecate legacy entrypoint remnants
3. refactor config-dependent state handling
4. refactor config-dependent reporting handling
5. keep runtime settings bridge until replacement is ready
6. remove `guards.py` later
