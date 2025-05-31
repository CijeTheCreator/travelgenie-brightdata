for name in agent, mcp, client, brightdata; do
  tmux new-session -d -s "$name"
done
