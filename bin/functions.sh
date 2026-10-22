describe() {
  echo "--- $1…"
}

squelch() {
  $@ > /dev/null 2>&1
}

log_for() {
  mkdir -p ./tmp/logs/
  touch ./tmp/logs/$1.log
  printf "./tmp/logs/$1.log"
}

daemonize() {
  $@
}

check_port() {
  if lsof -n -i :$1 > /dev/null; then
    printf "\nError! port $1 is already being used.\n"
    exit 1
  fi
}

pid_for() {
  mkdir -p ./tmp/pids
  touch "./tmp/pids/$1.pid"
  printf "./tmp/pids/$1.pid"
}

check_pid() {
  PID_FILE=$(pid_for $1)
  if ps -p $(<$PID_FILE) > /dev/null; then
    printf "\n Error! $1 already running \n"
    exit 1
  fi
}

git_branch_name() {
  set +u
  if [ -n "$CI" ]; then
    local branch=$BUILDKITE_BRANCH
  else
    local branch=$(git rev-parse --abbrev-ref HEAD)
  fi
  set -u
  printf "$branch"
}

kill_pid() {
  PID_FILE=$(pid_for $1)
  if ps -p $(<$PID_FILE) > /dev/null; then
    kill $(<$PID_FILE) > /dev/null
    describe "Killed $1 ($(<$PID_FILE))"
  fi
}

docker_services_up() {
  describe "Start docker services"
  docker-compose up -d
}

docker_services_down() {
  describe "Stop docker services"
  docker-compose down
}

brew_bundle_install() {
  if [ -f Brewfile ]; then
    brew bundle check || {
      describe "Install Homebrew dependencies"
      brew bundle
    }
  fi
}

asdf_bootstrap() {
  command -v asdf > /dev/null || {
    describe "Install asdf via Homebrew"
    brew install asdf
  }
}

asdf_add_plugins() {
  if [ -f .tool-versions ]; then
    describe "Add asdf language plugins"
    asdf plugin add python || true
    asdf plugin add uv || true
  fi
}

asdf_install_tools() {
  if [ -f .tool-versions ]; then
    describe "Install language versions"
    asdf install
  fi
}

asdf_update_plugins() {
  if [ -f .tool-versions ]; then
    describe "Update asdf language plugins"
    asdf plugin update --all
  fi
}

python_install_dependencies() {
  describe "Install python dependencies"
  uv sync --locked
}
