.PHONY: benchmark
benchmark:
	pytest test/perf \
		--benchmark-group-by="group,param:object_key_count" \
		--benchmark-warmup=on \
		--benchmark-warmup-iterations=10 \
		--benchmark-disable-gc

.PHONY: unit-test
unit-test:
	pytest test/unit --cov=fast_s3_url --cov-report xml:coverage.xml --cov-report term

.PHONY: integration-test
integration-test:
	pytest test/integration --cov=fast_s3_url --cov-report xml:coverage.xml --cov-report term
