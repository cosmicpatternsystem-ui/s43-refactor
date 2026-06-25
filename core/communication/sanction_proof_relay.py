class SanctionProofRelay:
    def __init__(self):
        self.peers = []  # List of connected peers

    def add_peer(self, peer):
        """Add a peer to the network."""
        if peer not in self.peers:
            self.peers.append(peer)

    def remove_peer(self, peer):
        """Remove a peer from the network."""
        if peer in self.peers:
            self.peers.remove(peer)

    def broadcast(self, message):
        """Send a message to all connected peers."""
        for peer in self.peers:
            self.send_message(peer, message)

    def send_message(self, peer, message):
        """Simulate sending a message to a peer."""
        print(f"Sending message to {peer}: {message}")

    def receive_message(self, message):
        """Handle incoming messages."""
        print(f"Received message: {message}")