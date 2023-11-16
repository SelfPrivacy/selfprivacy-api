{
  description = "SelfPrivacy API flake";

  inputs.nixpkgs.url = "github:nixos/nixpkgs";

  outputs = { self, nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      selfprivacy-graphql-api = pkgs.callPackage ./default.nix {
        pythonPackages = pkgs.python310Packages;
      };
    in
    {
      packages.${system}.default = selfprivacy-graphql-api;
      nixosModules.default = {
        imports = [
          (import ./nixos/module.nix self.packages.${system}.default)
          ./nixos/config.nix
        ];
      };
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
  nixConfig.bash-prompt = ''\n\[\e[1;32m\][\[\e[0m\]\[\e[1;34m\]SP devshell\[\e[0m\]\[\e[1;32m\]:\w]\$\[\[\e[0m\] '';
}
