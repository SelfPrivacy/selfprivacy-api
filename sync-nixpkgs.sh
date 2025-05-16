#! /usr/bin/env bash

# sync the version of nixpkgs used in the repo with one set in nixos-config 
nix flake lock --override-input nixpkgs nixpkgs --inputs-from "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=${1:-flakes}"
