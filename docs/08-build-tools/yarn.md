# Yarn

## [yarn-deduplicate](https://github.com/atlassian/yarn-deduplicate)

Cleans up yarn.lock by removing duplicates.

This package only works with Yarn v1. Yarn v2 supports package deduplication natively!

## nuke nodemodules

rm -rf node_modules/.yarn-integrity && yarn install
