{ pkgs, ... }:

{
  packages = with pkgs; [
    git
    busybox
    nodejs_22
  ];

  languages.python = {
    enable = true;
    package = pkgs.python313;
    venv.enable = true;
    uv = {
      enable = true;
      sync.enable = true;
    };
  };

  tasks = {
    "app:version" = {
      exec = ''
        ${pkgs.python313.interpreter} --version
      '';
    };
    "app:build" = {
      exec = ''
        uv export -o ./requirements.txt
        docker build -t omdv/ibkr-assistant:test .
      '';
    };
  };
}
