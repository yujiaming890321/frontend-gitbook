# Best Practices for Cryptography Components

|Compoment|Trait|
| --------- | --------------------------------- |
|Symmetric Encryption|Confidentiality|

|Mode of Operation|Trait|
| --------- | --------------------------------- |
|MAC|Integrity, Authenticity|
|Key Exchange|Confidentiality|
|Hash Function|Integrity|
|Digital Signature|Non-repudiation, Integrity, Authenticity|
|Asymmetric Encryption|Confidentiality, Authenticity|
|*AEAD|Confidentiality, Authenticity, Integrity|

* Confidentiality – Assuring data is only accessible to authorized entities.
* Integrity – Assuring data is not modified during transmission/storage by unauthorized entities.
* Authenticity – Assuring data is sent by authenticated entities.
* Non-repudiation – Assuring the sender cannot deny the message.
