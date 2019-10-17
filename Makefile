PROJECT = skedder
VIRTUAL_ENV = env
FUNCTION_NAME = skedder
AWS_REGION = us-east-1
FUNCTION_HANDLER = lambda_handler
LAMBDA_ROLE = arn:xxxxxxxxxxxxxx

# Default commands
install: virtual
build: clean_package build_package_temp copy_python remove_unused customizations zip

#create venv if not yet done
virtual:
	@echo "--> Setup and actiate virtualenv"
	if test ! -d "$(VIRTUAL_ENV)"; then \
		pip3 install virtualenv; \
		virtualenv $(VIRTUAL_ENV); \
	fi
	@echo ""

clean_package:
	rm -rf ./package/*

build_package_temp:
	mkdir -p ./package/tmp/lib
	cp -a ./$(PROJECT)/. ./package/tmp/

copy_python:
	cp -a lib/python3.7/site-packages/. ./package/tmp/;
	# if test -d $(VIRTUAL_ENV)/lib; then \
	# 	cp -a $(VIRTUAL_ENV)/lib/python3.7/site-packages/. ./package/tmp/; \
	# fi
	# if test -d $(VIRTUAL_ENV)/lib64; then \
	# 	cp -a $(VIRTUAL_ENV)/lib64/python3.7/site-packages/. ./package/tmp/; \
	# fi

remove_unused:
	rm -rf ./package/tmp/wheel*
	rm -rf ./package/tmp/easy-install*
	rm -rf ./package/tmp/setuptools*

customizations:
	cp ./credentials.json ./package/tmp/
	cp -r ./tmp ./package/tmp/

zip:
	cd ./package/tmp && zip -r ../$(PROJECT).zip .