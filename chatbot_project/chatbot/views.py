from django.shortcuts import render
from django.http import JsonResponse
# from Pipeline.pipe import Pipeline

def query_view(request):
    if request.method == "POST":
        user_query = request.POST.get('query')
        response = "working fine"  # for testing
        # response = Pipeline().process_query(user_query)
        return JsonResponse({'response': response})
    return render(request, 'chatbot/query_form.html')