{ pkgs ? import <nixpkgs> {} }:
pkgs.callPackage ./api.nix {}
