{
  description = "SelfPrivacy API application flake";

  inputs = {
    selfprivacy-nixos-config.url =
      "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git";

    # nixpkgs is inherited from selfprivacy-nixos-config
    # but can be overridden with `--override-input` option for nix build/flake
    nixpkgs.follows = "selfprivacy-nixos-config/nixpkgs";
  };

  outputs = { nixpkgs, ... }:
  let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
    selfprivacy-graphql-api = pkgs.callPackage ./default.nix {
      pythonPackages = pkgs.python310Packages;
    };
  in
  {
    packages.${system}.default = selfprivacy-graphql-api;
    devShells.${system}.default = pkgs.mkShell {
      inputsFrom = [ selfprivacy-graphql-api ];
      packages = with pkgs; [
        black
        rclone
        redis
        restic
      ];
      # FIXME is it still needed inside shellHook?
      # PYTHONPATH=${sp-python}/${sp-python.sitePackages}
      shellHook = ''
        # envs set with export and as attributes are treated differently.
        # for example. printenv <Name> will not fetch the value of an attribute.
        export USE_REDIS_PORT=6379
        pkill redis-server
        sleep 2
        setsid redis-server --bind 127.0.0.1 --port $USE_REDIS_PORT >/dev/null 2>/dev/null &
        # maybe set more env-vars
      '';
    };
  };
  nixConfig.bash-prompt-suffix = "[SP devshell] ";
}
