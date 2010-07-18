(function () { 
    
    /*
      
      `unicode aware`_ regexp char sets
      
      .. _`unicode aware`: http://bit.ly/14baJp
      
    */
    
    var new_line = '\u000a\u000d\u2028\u2029\u0085';
    var space = '\u0009\u000b\u000c\u0020\u00A0\u1680\u180E\u2000-\u200A\u202F\u205F\u3000';
    
    var ws = '[' + space + new_line + ']';
    var dot = '[^' + new_line + ']'; 
    
    var strip_expression = new RegExp('^(' + ws + ')+|(' + ws + ')+$', 'gm');
    var strip = function (s) {
      return s.replace(strip_expression, '');
    };
    
    var start_section_comment = new RegExp('<!-- section:(' + dot + '*) -->', 'gm');
    
    var get_section_content_by_id = function (doc) { /*
        
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
      
      var content = doc.content;
      
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
            section_content = strip(content.slice(0, end_pos));
            emit([doc.repository, doc._id, doc.path, doc.filename, section_id], section_content);
          }
        }
      }
      
    };
    
    var map = function (doc) {
      if (doc.doc_type == 'Document' && doc.content) {
        get_section_content_by_id(doc);
      }
    };
    
    return map;
    
})();