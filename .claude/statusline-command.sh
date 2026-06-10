#!/usr/bin/env bash
# Claude Code status line: context window usage display

input=$(cat)

# Extract values
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
remaining_pct=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')
input_tokens=$(echo "$input" | jq -r '.context_window.current_usage.input_tokens // empty')
ctx_size=$(echo "$input" | jq -r '.context_window.context_window_size // empty')
model=$(echo "$input" | jq -r '.model.display_name // empty')
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // empty')

# If no context data yet, show a minimal idle line
if [ -z "$used_pct" ] || [ -z "$ctx_size" ]; then
  dir=$(basename "$cwd")
  printf "\033[2m[%s] %s | context: idle\033[0m\n" "$model" "$dir"
  exit 0
fi

# Round percentages to integers
used_int=$(printf "%.0f" "$used_pct")
remaining_int=$(printf "%.0f" "$remaining_pct")

# Build a 20-char progress bar
bar_width=20
filled=$(( used_int * bar_width / 100 ))
empty=$(( bar_width - filled ))
bar=""
for i in $(seq 1 $filled);  do bar="${bar}#"; done
for i in $(seq 1 $empty);   do bar="${bar}-"; done

# Pick color based on usage: green < 60%, yellow < 80%, red >= 80%
if [ "$used_int" -ge 80 ]; then
  color="\033[31m"   # red
elif [ "$used_int" -ge 60 ]; then
  color="\033[33m"   # yellow
else
  color="\033[32m"   # green
fi
reset="\033[0m"
dim="\033[2m"

# Format token count as e.g. "45.2k" or "123k"
fmt_tokens() {
  local t="$1"
  if [ -z "$t" ] || [ "$t" = "null" ]; then echo "?"; return; fi
  if [ "$t" -ge 1000 ]; then
    printf "%.1fk" "$(echo "scale=1; $t / 1000" | bc)"
  else
    echo "$t"
  fi
}

used_fmt=$(fmt_tokens "$input_tokens")
total_fmt=$(fmt_tokens "$ctx_size")
dir=$(basename "$cwd")

printf "${dim}[${reset}${color}%s${reset}${dim}]${reset} ${dim}%s${reset} ${dim}|${reset} ${color}[%s]${reset} ${color}%s%%${reset} ${dim}used (%s/%s tokens) | %s%% remaining${reset}\n" \
  "$model" "$dir" "$bar" "$used_int" "$used_fmt" "$total_fmt" "$remaining_int"
