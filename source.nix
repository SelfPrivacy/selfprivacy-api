{
  runCommand,
  gettext,
  tailwindcss_4,
  src,
}:

runCommand "selfprivacy-api-source" {
  nativeBuildInputs = [ gettext tailwindcss_4 ];
} ''
  cp -r ${src} $out
  chmod -R +w $out

  tailwindcss -i $out/selfprivacy_api/userpanel/css/input.css -o $out/selfprivacy_api/userpanel/static/styles.css

  shopt -s nullglob
  for po in $out/selfprivacy_api/locale/*/LC_MESSAGES/messages.po; do
    msgfmt -o "''${po%.po}.mo" "$po"
  done
''
