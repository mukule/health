
    $(document).ready(function () {
        const makeField = $('#id_make');
        const modelField = $('#id_model');

        makeField.change(function () {
            const makeId = $(this).val();

            $.ajax({
                type: 'GET',
                url: '{% url "get_car_models" %}',  // Using the {% url %} template tag
                data: {
                    'make_id': makeId
                },
                success: function (data) {
                    modelField.empty();
                    if (data.length) {
                        for (let i = 0; i < data.length; i++) {
                            const model = data[i];
                            modelField.append($('<option></option>').attr('value', model.id).text(model.name));
                        }
                    } else {
                        modelField.append($('<option></option>').text('No models available'));
                    }
                },
                error: function (xhr) {
                    console.log('Error:', xhr.responseText);
                }
            });
        });
    });

