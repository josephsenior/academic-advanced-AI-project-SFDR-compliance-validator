import sys
try:
    import tokenizers
    print('tokenizers module:', tokenizers)
    print('__spec__:', getattr(tokenizers, '__spec__', None))
    spec = getattr(tokenizers, '__spec__', None)
    if spec:
        print('spec.name:', spec.name)
        print('spec.loader:', spec.loader)
except Exception as e:
    print('ERROR:', type(e).__name__, e)
    sys.exit(1)
