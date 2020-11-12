from crypto import KeyGenerator, BitcoinWallet


class Wallet:
    def __init__(
            self,
            private_key=None
    ):

        self.private_key = private_key or self.generate_private_key()
        self.public_key = self.private_to_public(self.private_key)
        self.address = self.public_to_address(self.public_key)

    def generate_private_key(self):
        kg = KeyGenerator()
        private_key = kg.generate_key()
        return private_key

    def private_to_public(self, private_key, compressed=True):
        if compressed:
            public_key = BitcoinWallet.private_to_compressed_public(private_key)
        else:
            public_key = BitcoinWallet.private_to_public(private_key)
        return public_key

    def public_to_address(self, public_key):
        address = BitcoinWallet.public_to_address(public_key)
        return address


if __name__ == "__main__":
    from ecdsa import SigningKey, SECP256k1
    from hashlib import sha256

    wallet = Wallet()
    private_key = bytearray.fromhex(wallet.private_key)

    # Generate sk & vk
    sk = SigningKey.from_string(private_key, curve=SECP256k1)
    vk = sk.verifying_key

    # sign & verify
    docu = b"message"
    digest = sha256(docu).digest()

    signature = sk.sign(digest)
    assert vk.verify(signature, digest)
