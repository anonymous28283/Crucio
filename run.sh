bench=../gi-benchmarks
name=$1
seed=$2
parser=$bench/$name/parse_${name}_darwin
train=$bench/$name/$name-train-$seed
test=$bench/$name/$name-test
echo $train
python3 infer.py $parser $train ./$name-$seed.log
python3 eval.py $test ./$name-$seed.log