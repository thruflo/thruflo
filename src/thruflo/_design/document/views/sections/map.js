(function () { 
    
    /*
      
      `unicode aware`_ regexp char sets
      
      .. _`unicode aware`: http://bit.ly/14baJp
      
    */
    
    var new_line = '\u000a\u000d\u2028\u2029\u0085';
    var space = '\u0009\u000b\u000c\u0020\u00A0\u1680\u180E\u2000-\u200A\u202F\u205F\u3000';
    
    var nl = '[' + new_line + ']';
    var sp = '[' + space + ']';
    var dot = '[^' + new_line + ']'; 
    
    /*
      
      unicode patched versions of `Showdown`_'s heading patterns:
      
      * `setext`_ h1: ``/^(.+)[ \t]*\n=+[ \t]*\n/gm``
      * `setext`_ h2: ``/^(.+)[ \t]*\n-+[ \t]*\n/gm``
      * `atx`_ h1-h6: ``/^(\#{1,6})[ \t]*(.+?)[ \t]*\#*\n/gm``
      
      .. _`Showdown`: http://attacklab.net/showdown/
      .. _`setext`: http://docutils.sourceforge.net/mirror/setext.html
      .. _`atx`: http://www.aaronsw.com/2002/atx/
      
    */
    
    // n.b.: we allow headings to match the end of doc as well as a new line at the
    // end of the line
    var setext_pattern = '^(' + dot + '+)' + sp + '*' + nl + '=+' + sp + '*(' + nl + '|$)';
    var setext = {
      'h1': new RegExp(setext_pattern, 'gm'),
      'h2': new RegExp(setext_pattern.replace('=', '-'), 'gm')
    };
    
    var atx_pattern = '^(\#{1,6})' + sp + '*(' + dot + '+)' + sp + '*\#*(' + nl + '|$)';
    var atx = new RegExp(atx_pattern, 'gm');
    
    /*
      
      And patterns to split text against:
      
          <hn>Heading Text</hn>
      
    */
    
    var split_pattern = '^<h{i}>(' + dot + '+)<\/h{i}>' + sp + '*' + nl;
    var split = {};
    for (i = 1; i < 7; i++) {
      split['h' + i] = new RegExp(split_pattern.replace(/h\{i\}>/g, 'h' + i + '>'), 'gm');
    }
    
    var recursively_emit = function (text, level, key) { /*
        
        Recursive function to split:
        
            # Test Doc 1
            
            ## Section Foo
            
            foo
            
            ### Sub Section Blah
            
            blah
            
            ## Section Bar
            
            bar
        
        Into:
        
            [{
                "key": ["...", 0, "Test Doc 1", 0, null, 0, null, ...],
                "value":"## Section Foo\n\nfoo\n\n### Sub Section Blah\n\nblah\n\n## Section Bar\n\nbar"
              }, {
                "key":["...", 0, "Test Doc 1", 0, "Section Foo", 0, null, ...],
                "value":"foo\n\n### Sub Section Blah\n\nblah\n\n"
              }, {
                "key":["...", 0, "Test Doc 1", 0, "Section Foo", 0, "Sub Section Blah", ...],
                "value":"blah\n\n"
              }, {
                "key":["...", 0, "Test Doc 1", 2, "Section Bar", 0, null, ...],
                "value":"bar"
              }
            ]
        
        One heading level (h1 - h6) at a time.
        
      */
      
      var hn = 'h' + level;
      var _handle_setext_match = function (whole_match, first_match) {
        return '<' + hn + '>' + first_match + '</' + hn + '>\n';
      };
      var _handle_atx_match = function (whole_match, first_match, second_match) {
        var l = first_match.length;
        if (l == level) {
          return '<h' + l + '>' + second_match + '</h' + l + '>\n';
        }
        else {
          return whole_match;
        }
      };
      
      /*
        
        If we're handling level 1 or 2, replace Setext_ 
        ``H1``s and ``H2``s:
        
            Heading 1
            =========
            
            Heading 2
            ---------
        
        With ``<hn>Heading Text</hn>`` markup.
        
      */
      
      if (setext.hasOwnProperty(hn)) {
        text = text.replace(setext[hn], _handle_setext_match);
      }
      
      /*
        
        Then replace atx_ ``H1`` to ``H6``s:
        
            # Heading 1
            # Heading 1 #
            ...
            ###### Heading 6
            ###### Heading 6 ######
        
        With the same ``<hn>Heading Text</hn>`` markup.
        
      */
      
      text = text.replace(atx, _handle_atx_match);
      
      /*
        
        Now split into parts, so:
        
            ## Heading
            
            Foo bar
            
            ## Heading Again
            
            Dolores
        
        Becomes:
        
            [[""Heading", "\n", "Foo bar\n\n""], ["Heading Again", "\n", "Dolores"]]
        
      */
      
      var parts = text.split(split[hn]).slice(1);
      
      /*
        
        Which we then yeild not only in items:
        
            ["Heading", "Foo bar\n\n", "Heading Again", "Dolores"]
        
        But also recursively with children, ala:
        
            [[""Heading", content, recursively_emit(content, next_level)], ...]
        
        Except that instead of building a nested list, we emit rows to the view
        index instead:
        
            [{
                "key": ["...", 0, "...", 0, "Heading", ...],
                "value":"Foo bar\n\n"
              }, {
                "key":["...", 0, "...", 2, "Heading Again", ...],
                "value":"Dolores"
              }
            ]
        
        Where each row is:
        
            "key": [
              // repository id
              "c18862966c9a294c0f4ed6558a63540b", 
              // h1 index
              0, 
              // h1 text
              "Test Doc 1", 
              // h2 index
              0, 
              // h2 text
              null, 
              
              ...
              
              // h6 index
              0, 
              // h6 text
              null 
            ],
            // the full markdown text the section contains
            // including the raw markdown for sub sections
            "value": "## Section Foo\n\nfoo\n\n### Sub Section Blah\n\nblah\n\n## Section Bar\n\nbar"
        
      */
      
      // we work with a copy of the key and the parts
      var key = key.slice(0);
      
      // clearing anything after this level
      var key_length = key.length;
      var heading_index = (level * 2);
      var sort_counter_index = heading_index - 1;
      for (i = heading_index + 1; i < key_length; i = i + 2) {
        // n.b.: ``0`` and ``null`` are explicit default values
        // see ``_six_zero_null_pairs`` below...
        if (key[i] != 0) {
          key[i] = 0;
          key[i + 1] = null;
        }
        else {
          break;
        }
      }
      
      var i,
          item, 
          heading, 
          value, 
          parts_length = parts.length;
      var next_level = level + 1;
      
      if (parts_length) {
        for (i = 0; i < parts_length; i = i + 2) {
          item = parts.slice(i, i + 2);
          heading = item[0];
          value = item[1];
          // build the key
          key[heading_index] = heading;
          // n.b.: inserting ``i`` into the key means we can sort the emitted 
          // rows in the same order we're looping through here
          key[sort_counter_index] = i;

          // emit
          emit(key.slice(0), value);
          
          // recurse
          if (value && next_level < 7) {
            recursively_emit(value, next_level, key);
          }
        }
      }
      
    };
    
    /*
      
      Map function for the couchjs view engine
      
    */
    
    var _six_zero_null_pairs = [0, null, 0, null, 0, null, 0, null, 0, null, 0, null];
    var map = function (doc) {
      if (doc.doc_type == 'Document') {
        var heading_level = 1;
        var key = [doc.repository].concat(_six_zero_null_pairs);
        recursively_emit(doc.content, heading_level, key);
      }
    };
    
    return map;
    
})();