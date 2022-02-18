# TODO

- [ ] wrap logger commands

eg in BigLib.
but still take the same arg format `("ff %s", s)` so we can mix and match with system logging as needed

replace all these checks:

```
    if BigLib.debug:
            logging.debug('query_one result: %s', blob)
```


## conversation clustering

- based on transformed data
- normalize schema
- utterance/intent/pagename

prev page and exit page

group conversations into "clusters"

## Questions on ingester

- why using 'transcript_id' ? it requires renaming columns... session_id is more globally used too...
- turn is also shorter than 'position' ?

really suggest separating "ingester" and stuff to do queries on the actual agent into separate classes

therefore dont need creds or agent_type for ingester

have a separate class that combines both actions

we can keep config stuff all in a single file?
(this could be editable via a UI later?)
i'm using a dataclass for this now so we get typechecking
https://docs.python.org/3/library/dataclasses.html#module-dataclasses
see config/client_config.py for concrete example
