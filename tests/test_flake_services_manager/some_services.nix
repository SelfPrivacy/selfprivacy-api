{
  description = "SelfPrivacy NixOS PoC modules/extensions/bundles/packages/etc";


  inputs.bitwarden.url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/bitwarden";

  inputs.gitea.url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/gitea";

  inputs.jitsi-meet.url = "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/jitsi-meet";

  outputs = _: { };
}
