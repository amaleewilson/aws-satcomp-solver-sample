# /bin/sh
cd base
docker build -t cvc5_base .
cd ../leader
docker build -t cvc5:leader .
cd ../worker
docker build -t cvc5:worker .
