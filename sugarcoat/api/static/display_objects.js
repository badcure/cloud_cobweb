function display_json_new(content) {

    if ((typeof content) == "string") {
        return '<span class="json_string_complete">"<span class="json_string_content">' + content + '</span>"</span>'
    }
    if ((typeof content) == "object") {
        var result_string =  '<span class="json_object_complete">';

        jQuery.each(content, function(key, value) {
            result_string = result_string + key;
            result_string = result_string + display_json_new(value);
        });
        result_string = result_string + '</span>';
        return result_string
    }
    return content;

}