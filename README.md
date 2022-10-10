# Phononscan
A website to determine if an ethereum address is a phonon.  For addresses that are not phonons, the script will check transaction history to determine if the address has created or redeemed phonons.  By design, it is impossible to tell for certain if an address is a phonon, so the script just points out if an address or transaction *could* be a phonon.

Currently only runs on the (now defunct) Rinkeby testnet.  Build with python using Flask and Web3.py.
