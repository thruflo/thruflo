/*
  
  thruflo.markdown namespace
  
  
*/

var thruflo;

if (typeof(thruflo) == 'undefined') {
  thruflo = {};
}

if (!thruflo.hasOwnProperty('markdown')) {
  thruflo['markdown'] = {};
}

/*
  
  provide:
  
  * thruflo.markdown.get_sections(doc);
  * thruflo.markdown.get_first_title(doc_content);
  
  
*/

(function ($) { 
    
    /*
      
      `unicode aware`_ regexp char sets
      
      .. _`unicode aware`: http://bit.ly/14baJp
      
    */
    
    var new_line = '\u000a\u000d\u2028\u2029\u0085';
    var space = '\u0009\u000b\u000c\u0020\u00A0\u1680\u180E\u2000-\u200A\u202F\u205F\u3000';
    
    var nl = '[' + new_line + ']';
    var sp = '[' + space + ']';
    var wp = '[' + new_line + space + ']';
    var dot = '[^' + new_line + ']'; 
    
    
    /*
      
      ``$.rtrim`` and ``$.ltrim``
      
    */
    
    /*
    var rtrim_expression = new RegExp('(' + wp + ')+$', 'm');
    $.rtrim = function (s) {
      return s.replace(rtrim_expression, '');
    };
    
    var ltrim_expression = new RegExp('^(' + wp + ')+', 'm');
    $.ltrim = function (s) {
      return s.replace(ltrim_expression, '');
    };
    */
    
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
    var i;
    for (i = 1; i < 7; i++) {
      split['h' + i] = new RegExp(split_pattern.replace(/h\{i\}>/g, 'h' + i + '>'), 'gm');
    }
    
    /*
      
      thruflo.markdown.section function
      
    */
    
    var _six_zero_null_pairs = [0, null, 0, null, 0, null, 0, null, 0, null, 0, null];
    
    var recursively_section = function (text, level, key) { /*
        
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
        
            [[""Heading", content, recursively_section(content, next_level)], ...]
        
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
      key = key.slice(0);
      
      // clearing anything after this level
      var i;
      var key_length = key.length;
      var heading_index = (level * 2);
      var sort_counter_index = heading_index - 1;
      for (i = heading_index + 1; i < key_length; i += 2) {
        // n.b.: ``0`` and ``null`` are explicit default values
        // see ``_six_zero_null_pairs`` above...
        if (key[i] != 0) {
          key[i] = 0;
          key[i + 1] = null;
        }
        else {
          break;
        }
      }
      
      var item, 
          items = [],
          heading, 
          value, 
          next_level = level + 1,
          parts_length = parts.length;
      if (parts_length) {
        for (i = 0; i < parts_length; i += 2) {
          item = parts.slice(i, i + 2);
          heading = item[0];
          value = item[1];
          // build the key
          key[heading_index] = heading;
          // n.b.: inserting ``i`` into the key means we can sort the emitted 
          // rows in the same order we're looping through here
          key[sort_counter_index] = i;
          // recurse
          if (value && next_level < 7) {
            items.push([key.slice(0), value, recursively_section(value, next_level, key)]);
          }
          else {
            items.push([key.slice(0), value, []]);
          }
        }
      }
      
      return items;
      
    };
    
    thruflo.markdown.get_sections = function (doc) {
      var heading_level = 1;
      var key = [doc.repository].concat(_six_zero_null_pairs);
      return recursively_section(doc.content, heading_level, key);
    };
    
    /*
      
      thruflo.markdown.get_first_title function
      
    */
    
    var leading_whitespace = new RegExp('^' + wp);
    var leading_settext_h1 = new RegExp(setext_pattern);
    var leading_atx_h1 = new RegExp(atx_pattern.replace('{1,6}', ''));
    
    thruflo.markdown.get_first_title = function (content) { /*
        
        Extracts document title from the opening H1
        in the markdown content.
        
        If the first non-whitespace in the document 
        content isn't a valid setext or atx H1 then
        returns null.
        
        
      */
      
      // strip any leading whitespace
      content = content.replace(leading_whitespace, '');
      
      // the document should start with the h1,
      // so we needn't parse the whole thing
      if (content.length > 500) {
        content = content.slice(0, 500);
      }
      
      var title = null;
      var groups = leading_atx_h1.exec(content);
      if (groups) {
        title = groups[2];
      }
      else {
        groups = leading_settext_h1.exec(content);
        if (groups) {
          title = groups[1];
        }
      }
      
      return title;
      
    };
    
    /*
      
      thruflo.markdown.get_section_ids function
      
    */
    
    var start_section_comment = new RegExp('<!-- section:(' + dot + '*) -->', 'gm');
    
    thruflo.markdown.get_section_content_by_id = function (content) { /*
        
        Extracts the ``<!-- section:... --> ... <!-- end section -->`` sections
        and returns them, in the order the appear in the document, in dicts
        with ``{'id': '...', 'content': '...'}``.
        
        E.g.:
        
            # Hello
            
            <!-- section:test_doc_one.md#Test Doc One##Footer ord:0:2 -->
            
            I love you
            
            <!-- end section:test_doc_one.md#Test Doc One##Footer ord:0:2 -->
            
            Won't you tell me your name
            
        Returns:
        
            [{
                'id': 'test_doc_one.md#Test Doc One##Footer ord:0:2', 
                'content': 'I love you'
              }
            ]
        
      */
      
      var results = [];
      
      console.log('get_section_content_by_id content');
      console.log(content);
      
      var start_comments = content.match(start_section_comment);
      if (start_comments) {
        var i, 
            l = start_comments.length,
            start_comment,
            section_id,
            end_comment,
            start_pos,
            end_pos,
            section_content,
            match_content,
            match_string,
            counter = 1,
            match,
            pos,
            is_end_comment;
        for (i = 0; i < l; i++) {
          start_comment = start_comments[i];
          section_id = start_comment.slice(13, -4);
          
          start_pos = content.indexOf(start_comment) + start_comment.length;
          end_pos = 0;
          
          /* 
            
            we have to handle nested comments, e.g.:
            
            start abc
              start abc
                start abc
                end abc
              end abc
            end abc
            
            so we keep a counter of the number of ``end``s we're looking
            for and walk the tree, incrementing it when we hit a start
            and decrementing when we hit an end, until / unless the counter
            is one, in which case we have our matching comment:
            
            start abc # n = 1
              start abc # incr, so n = 2
                start abc # incr, so n = 3
                end abc # n = 3, so decr
              end abc # n = 2, so decr
            end abc # n = 1, bingo :)
            
            @@ how to handle pooped nesting?
          
          */
          
          content = content.slice(start_pos);
          
          match_content = content;
          match_string = ' section:' + section_id + ' -->';
          counter = 1;
          while (true) {
            match = match_content.match(match_string);
            if (!match) { 
              break; 
            }
            else {
              pos = match_content.indexOf(match);
              is_end_comment = match_content.substr(pos-3, 3) == 'end';
              if (is_end_comment) {
                if (counter == 1) { // bingo :)
                  end_pos = content.indexOf(match_content) + pos + match.length - 9;
                  break;
                }
                else { // decr
                  counter = counter - 1;
                }
              }
              else { // incr
                counter = counter + 1;
              }
              match_content = match_content.slice(pos + match.length);
            }
          }
          if (end_pos) {
            section_content = $.trim(content.slice(0, end_pos));
            results.push({'id': section_id, 'content': section_content});
          }
        }
      }
      
      return results;
      
    };
    
    var re_escape = function (str) {
      return str.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, "\\$&");
    };
    
    thruflo.markdown.get_updated_dependency_content = function(doc_content, section_id, section_content) { /*
        
        overwrites ``doc_content``s dependency section's that match ``section_id``
        with ``section_content``
        
      */
      
      console.log('update_dependency_content ' + section_id);
      console.log(section_content);
      
      var content = doc_content;
      var start_comment = new RegExp(
        '\<\!\-\-\ section\:' + re_escape(section_id) + '\ \-\-\>', 'gm'
      );
      var all_comments = new RegExp(
        '\ section\:' + re_escape(section_id) + '\ \-\-\>', 'm'
      );
      var start_comments = content.match(start_comment);
      console.log('start_comments');
      console.log(start_comments);
      if (start_comments) {
        var i, 
            l = start_comments.length,
            start_comment,
            section_id,
            end_comment,
            start_pos,
            total_start_pos = 0,
            end_pos,
            match_content,
            match_string,
            counter = 1,
            match,
            pos,
            is_end_comment;
        for (i = 0; i < l; i++) {
          start_comment = start_comments[i];
          section_id = start_comment.slice(13, -4);
          console.log('section_id');
          console.log(section_id);
          start_pos = content.indexOf(start_comment) + start_comment.length;
          end_pos = 0;
          content = content.slice(start_pos);
          total_start_pos += start_pos;
          match_content = content;
          counter = 1;
          while (true) {
            console.log('start_pos');
            console.log(start_pos);
            console.log('total_start_pos');
            console.log(total_start_pos);
            match = match_content.match(all_comments);
            if (!match) { 
              console.log('*');
              break; 
            }
            else {
              console.log('**');
              pos = match_content.indexOf(match);
              is_end_comment = match_content.substr(pos-3, 3) == 'end';
              if (is_end_comment) {
                console.log('***');
                if (counter == 1) { // bingo :)
                  console.log('****');
                  end_pos = content.indexOf(match_content) + pos - 8;
                  break;
                }
                else { // decr
                  console.log('*****');
                  counter = counter - 1;
                }
              }
              else { // incr
                console.log('******');
                counter = counter + 1;
              }
              match_content = match_content.slice(pos + match.length);
            }
          }
          console.log('end_pos: ' + end_pos);
          if (end_pos) {
            var start_insert = total_start_pos;
            var end_insert = total_start_pos + end_pos;
            console.log('insert at: ' + start_insert + ', ' + end_insert);
            console.log('existing substring at that pos');
            console.log(doc_content.substr(start_insert, end_insert));
            console.log('the text we want to insert');
            console.log(section_content);
            doc_content = [
              doc_content.slice(0, start_insert),
              '\n\n',
              section_content,
              '\n\n',
              doc_content.slice(end_insert)
            ].join('');
          }
        }
      }
      return doc_content;
    };
    
})(jQuery);