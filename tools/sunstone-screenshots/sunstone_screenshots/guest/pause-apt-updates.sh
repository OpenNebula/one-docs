set -eu
if [ -d /etc/apt/apt.conf.d ]; then
    command -v systemctl >/dev/null || {
        echo 'The APT update guard requires systemd in this lab.' >&2
        exit 1
    }
    echo 'Pausing scheduled APT updates in this disposable lab.'
    printf '%s\n' 'APT::Periodic::Enable "0";' > /etc/apt/apt.conf.d/99sunstone-screenshot-lab
    for timer in apt-daily.timer apt-daily-upgrade.timer; do
        load_state=$(systemctl show "$timer" --property=LoadState --value)
        if [ "$load_state" != not-found ]; then
            systemctl stop "$timer"
        fi
    done
    # Masking prevents new jobs without terminating an update already in progress.
    systemctl mask apt-daily.timer apt-daily-upgrade.timer apt-daily.service apt-daily-upgrade.service
    for service in apt-daily.service apt-daily-upgrade.service; do
        while :; do
            update_state=$(systemctl show "$service" --property=ActiveState --value)
            case "$update_state" in
                inactive|failed) break ;;
                active|activating|deactivating|reloading|refreshing|maintenance)
                    echo "Waiting for $service ($update_state) to finish; package processes are left running."
                    sleep 2
                    ;;
                *)
                    echo "Unexpected state for $service: $update_state; refusing to start miniONE." >&2
                    exit 1
                    ;;
            esac
        done
    done
    echo 'Scheduled APT jobs are idle; continuing lab installation.'
else
    echo 'Skipping the APT update guard: this guest does not use APT.'
fi
