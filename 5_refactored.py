#-*- coding:utf-8 -*-
import sys,os, BaseHTTPServer

class ServerException(Exception):
    pass

#------------------------------------------------------------------------------
class base_case(object):
    """Parent for case handlers"""
    
    def handle_file(self,handler,full_path):
        try:
            with open(full_path,'rb')as reader:
                content=reader.read()
                handler.send_content(content)
        except IOError as msg:
            msg="'{0}' cannot be read: {1}".format(full_path,msg)
            handler.handle_error(msg)
    
    def index_path(self,handler):
        return os.path.join(handler.full_path,'index.html')
    
    def test(self,handler):
        assert False,'Not implemented'
        
    def act(self,handler):
        assert False,'Not implemented'


#------------------------------------------------------------------------------


class case_no_file(base_case):
    
    def test(self,handler):
        return not os.path.exists(handler.full_path)
    
    def act(self,handler):
        raise ServerException("'{0}' not found".format(handler.path))
    
#------------------------------------------------------------------------------

class case_cgi_file(base_case):
    
    def run_cgi(self,handler):
        cmd="python "+handler.full_path
        child_stdin,child_stdout=os.popen2(cmd)
        child_stdin.close()
        data=child_stdout.read()
        child_stdout.close()
        self.send_content(data)
    
    def test(self,handler):
        return os.path.isfile(handler.full_path) and \
            handler.full_path.endswith('.py')
    
    def act(self,handler):
        self.run_cgi(handler)

#------------------------------------------------------------------------------

class case_existing_file(base_case):
    def test(self,handler):
        return os.path.isfile(handler.full_path)
    
    def act(self,handler):
        handler.handle_file(handler.full_path)
        
#------------------------------------------------------------------------------
        
class case_directory_index_file(base_case):

    def test(self,handler):
        return os.path.isdir(handler.full_path)and \
            os.path.isfile(self.index_path(handler))
    def act(self,handler):
        self.handle_file(self.index_path(handler))
        
#------------------------------------------------------------------------------
        
class case_directory_no_index_file(base_case):
    Listing_Page="""\
        <html>
        <body>
        <ul>
        {0}
        </ul>
        </body>
        </html>    
    """
    def list_dir(self,full_path):
        try:
            entries=os.listdir(full_path)
            bullets=['<li>{0}</li>'.format(e) for e in entries if not e.startswith('.')]
            page =self.Listing_Page.format('\n'.join(bullets))
            self.send_content(page)
        except OSError as msg:
            msg="'{0}' cannot be listed:{1}".format(self.path,msg)
            self.handle_error(msg)
            
    def test(self,handler):
        return os.path.isdir(handler.full_path) and \
            not os.path.isfile(self.index_path(handler))
            
    def act(self,handler):
        handler.list_dir(handler.full_path)

#------------------------------------------------------------------------------

        
class case_always_fail(base_case):
    
    def test(self,handler):
        return True
    
    def act(self,handler):
        raise ServerException("Unkown object '{0}'".format(handler.path))
    
#------------------------------------------------------------------------------
    

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    
    '''
    if requested a file exist,then serverd.
    else post a Error page.
    '''
    
    Error_Page="""\
    <html>
    <body>
    <h1>Error accessing {path}</h1>
    <p>{msg}</p>
    </body>
    </html>
    """
    

    
    Cases=[case_no_file(),
           case_cgi_file(),
           case_existing_file(),
           case_directory_index_file(),
           case_directory_no_index_file(),
           case_always_fail()]
    
    
    def do_GET(self):
        try:
            
            self.full_path=os.getcwd()+self.path
            
            for case in self.Cases:
                if case.test(self):
                    case.act(self)
                    break
            
        except Exception as msg:
            self.handle_error(msg)
    
            


    def handle_error(self,msg):
        content=self.Error_Page.format(path=self.path,msg=msg)
        self.send_content(content,404)
        
    
        
    def send_content(self,page,status=200):
        self.send_response(status)
        self.send_header("Content-type","text/html")
        self.send_header("Content-Length",str(len(page)))
        self.end_headers()
        self.wfile.write(page)
        

#------------------------------------------------------------------------------


if __name__=='__main__':
    serverAddress=('',8080)
    server=BaseHTTPServer.HTTPServer(serverAddress,RequestHandler)
    server.serve_forever()