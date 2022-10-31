aws --profile blab ecr get-login-password --region us-west-1 | docker login --username AWS --password-stdin 127312632904.dkr.ecr.us-west-1.amazonaws.com/cvc5-cloud-leader

aws --profile blab ecr get-login-password --region us-west-1 | docker login --username AWS --password-stdin 127312632904.dkr.ecr.us-west-1.amazonaws.com/cvc5-cloud-worker

cd /Users/amaleewilson/aws-satcomp-solver-sample/leader
docker build -t cvc5:leader .
docker tag cvc5:leader 127312632904.dkr.ecr.us-west-1.amazonaws.com/cvc5-cloud-leader
docker push 127312632904.dkr.ecr.us-west-1.amazonaws.com/cvc5-cloud-leader


cd /Users/amaleewilson/aws-satcomp-solver-sample/worker
docker build -t cvc5:worker .
docker tag cvc5:worker 127312632904.dkr.ecr.us-west-1.amazonaws.com/cvc5-cloud-worker
docker push 127312632904.dkr.ecr.us-west-1.amazonaws.com/cvc5-cloud-worker
