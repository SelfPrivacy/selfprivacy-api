{ pkgs }:

let
  zshWithPlugins = pkgs.zsh.overrideAttrs (oldAttrs: {
    postInstall = oldAttrs.postInstall + ''
      # Create symlinks for plugins in $out/share
      mkdir -p $out/share/zsh/plugins
      ln -s ${pkgs.zsh-autosuggestions}/share/zsh-autosuggestions $out/share/zsh/plugins/autosuggestions
      ln -s ${pkgs.zsh-syntax-highlighting}/share/zsh-syntax-highlighting $out/share/zsh/plugins/syntax-highlighting
    '';
  });
in
{
  shell = zshWithPlugins;
  shellSetup = ''
    # create .zshrc file if it doesnt exist
    if [ ! -f ~/.zshrc ]; then
      echo "Creating a default .zshrc file..."
      touch ~/.zshrc
    fi

    # add zsh-autosuggestions and zsh-syntax-highlighting in zshrc
    if ! grep -q "source .*zsh-autosuggestions.zsh" ~/.zshrc; then
      echo "Adding zsh-autosuggestions plugin to .zshrc..."
      echo "source ${zshWithPlugins}/share/zsh/plugins/autosuggestions/zsh-autosuggestions.zsh" >> ~/.zshrc
    fi
    if ! grep -q "source .*zsh-syntax-highlighting.zsh" ~/.zshrc; then
      echo "Adding zsh-syntax-highlighting plugin to .zshrc..."
      echo "source ${zshWithPlugins}/share/zsh/plugins/syntax-highlighting/zsh-syntax-highlighting.zsh" >> ~/.zshrc
    fi
  '';
}
