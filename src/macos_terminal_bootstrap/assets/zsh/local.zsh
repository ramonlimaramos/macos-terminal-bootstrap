# Local non-secret shell customizations.
# Put tokens, private keys, and customer credentials in:
#   ~/.config/ramon-terminal/zsh/secrets.zsh

alias gndir="cd ~/Developer/podium/garden"
alias garden-update="gndir && git pull && garden update-remote all"
alias garden-resume="gndir && ./unpause.sh"
alias garden-iex="gndir && ./elixir_debug.sh"
alias phx="source .env && iex -S mix phx.server"
alias mix-test="MIX_ENV=test mix test"

export GARDEN_NAMESPACE="ramon-ramos"
export GARDEN_CLUSTER="g-sae1"
export VIRTUAL_ENV_DISABLE_PROMPT=1
export GIT_HTTP_LOW_SPEED_LIMIT=0
export GIT_HTTP_LOW_SPEED_TIME=30

garden-log() {
  AWS_ACCESS_KEY_ID=""
  AWS_REGION=""
  AWS_SECRET_ACCESS_KEY=""

  SERVICE_NAME=$1
  gndir && echo "Getting logs for $SERVICE_NAME" && garden logs "$SERVICE_NAME" -f
}

dz_ignore() {
  echo "" > .dialyzer.ignore-warnings
  MIX_ENV=dev mix dialyzer --format dialyzer 2> .temp.dialyzer.ignore-warnings
  sed -r "s/\x1B\[([0-9]{1,3}(;[0-9]{1,3})*)?[mGK]//g" .temp.dialyzer.ignore-warnings \
    | sed "/done (/,\$d" > .dialyzer.ignore-warnings
  rm .temp.dialyzer.ignore-warnings
  MIX_ENV=dev mix dialyzer --format dialyzer
}

flip_azeroth() {
  current_folder=$PWD
  cd "$HOME/Developer/podium/halberd" || return
  pipeline -c "flags.flip --for org --uids $1 --slugs webchat_azeroth_data_transition_complete" halberd
  cd "$current_folder" || return
}

rollout_azeroth() {
  current_folder=$PWD
  cd "$HOME/Developer/podium/halberd" || return
  pipeline -c "flags.bump --for org --step $1 --slug webchat_azeroth_data_transition_complete" halberd
  cd "$current_folder" || return
}
