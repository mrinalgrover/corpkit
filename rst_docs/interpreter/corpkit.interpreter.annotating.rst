Annotating your corpus
========================

Another thing you might like to do is add metadata or annotations to your corpus. This can be done by simply editing corpus files.

You can also automate annotation, however. To do this, you first run a ``search`` command and generate a ``concordance`.

Then, you edit and colour this concordance however you like.

Then, you can use the ``annotate`` command. It works a lot like the ``mark``, ``keep``, and ``del`` commands to begin with, but has some special syntax at the end.

Tagging sentences
-------------------

The first way of annotating is to add a **tag** to one or more sentences:

.. code-block:: shell

   > search corpus for pos matching NNP and word matching 'daisy'
   > annotate m matching '^daisy$' with tag 'has_daisy'

.. code-block:: shell

   > search corpus for governor-function matching nsubjpass showing governor-lemma and lemma
   > annotate all with tag 'passive'

If you try to run this code, you actually get a `dry run`, showing you what would be modified in your corpus. Once you're happy with it, you can do ``toggle annotation`` to turn file writing on, and then run the previous line again (use the up arrow to get it!).

Creating fields and values
-----------------------------

More complex than adding tags is adding **fields** and **values**. This creates a new metadata category with multiple possible realisations. Below, we tag an sentence sentences based on their containing certain kinds of processes

.. code-block:: shell

   > search corpus for function matching roles.process showing lemma
   > mark m matching processes.verbal red
   # annotate by colour
   > annotate red with field as process \
   ...    and value as 'verbal'
   # annotate without colouring first
   > annotate m matching processes.mental with field as process \
   ...    and value as 'mental'

You can also use ``m`` as the value, which passes in the text from the middle column of the concordance.

.. code-block:: shell

   > search corpus for pos matching NNP showing word
   > annotate m matching [gatsby, daisy, tom] \
   ...    with field as character and value as m

The moment these values have been added to your text, you can do really powerful things with them. You can, for example, use them as subcorpora, or use them as filters for the sentences being processed.

.. code-block:: shell

   > set subcorpora as process
   > set skip character as 'gatsby'
   > set skip passive tag

Now, the subcorpora will be the different processes (*verbal*, *mental* and *none*), and any sentence annotated as containing the ``gatsby`` ``character``, or the ``passive`` ``tag``, will be ignored.
