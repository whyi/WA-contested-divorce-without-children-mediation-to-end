deployment_output() {
  if [[ -n "${UAT_DEPLOYMENT_OUTPUTS_JSON:-}" ]]; then
    python3 "$script_dir/deployment_config.py" "$1"
  else
    terraform -chdir="$script_dir" output -raw "$1"
  fi
}
