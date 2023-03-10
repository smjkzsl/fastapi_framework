import inspect
import re
import types
from collections import defaultdict
from functools import wraps, update_wrapper
from typing import Callable, Dict, Set, Type
import copy
import typing_inspect
from fastapi import APIRouter,Request,Response
from fastapi_utils.cbv import cbv

controller_re = re.compile("([\\w]+)Controller")
snake_case_re = re.compile("(?<!^)(?=[A-Z][a-z])")

TEMPLATE_PATH_KEY = "__template_path__"
VER_KEY = "__custom_version__"
PATH_KEY = "__custom_path__"
METHOD_KEY = "__custom_method__"
KWARGS_KEY = "__custom_kwargs__"
SIGNATURE_KEY = "__saved_signature__"
ARGS_KEY = "__custom_args__"
AUTH_KEY="__auth__"


class ControllerBase:
    """ """
    
    pass


CBType = Type[ControllerBase]
CBTypeSet = Set[CBType]


def _get_leaf_controllers(controller_base: CBType) -> CBTypeSet:
    """

    Args:
      controller_base: Type[ControllerBase]:

    Returns:

    """
    controllers_to_process = controller_base.__subclasses__()
    controllers = set()

    while len(controllers_to_process) > 0:
        controller_to_process = controllers_to_process.pop()

        controller_subclasses = controller_to_process.__subclasses__()

        if len(controller_subclasses) > 0:
            controllers_to_process.extend(controller_subclasses)
        else:
            controllers.add(controller_to_process)

    return controllers


def _compute_path(route_path: str, controller_name: str, path_template_prefix: str, version: str) -> str:
    """

    Args:
      route_path: str:
      controller_name: str:
      path_template_prefix: str:
      version: str:

    Returns:

    """
    controller_name = controller_re.match(controller_name).group(1)
    snake_case_controller_name = snake_case_re.sub("_", controller_name)

    return f"{path_template_prefix}{route_path}" \
        .replace("{controller}", snake_case_controller_name.lower()) \
        .replace("{version}", version)


def _get_routes_in_controller(controller: Type[ControllerBase]):
    """

    Args:
      controller: Type[ControllerBase]:

    Returns:

    """
    routes_dict = defaultdict(dict)

    controller_hierarchy = {controller}

    while len(controller_hierarchy) > 0:
        cls = controller_hierarchy.pop()

        members = filter(
            lambda x: not x[0].startswith("_") and inspect.isfunction(x[1]),
            inspect.getmembers(cls))

        for name, member in members:
            path_attr = getattr(member, PATH_KEY, None)

            if not routes_dict.get(name, {}).get(PATH_KEY, None):
                if not path_attr:
                    controller_hierarchy.add(cls.__base__)
                else:
                    routes_dict[name][PATH_KEY] = path_attr
                    routes_dict[name][METHOD_KEY] = getattr(member, METHOD_KEY, None)
                    routes_dict[name][KWARGS_KEY] = getattr(member, KWARGS_KEY, None)
                    routes_dict[name][ARGS_KEY] = getattr(member, ARGS_KEY, None)

    return routes_dict


def _get_generic_type_var_dict(controller: Type[ControllerBase]) -> Dict:
    """

    Args:
        controller:

    Returns:

    """
    generic_values = []

    generic_bases = typing_inspect.get_generic_bases(controller)

    for generic_base in generic_bases:
        generic_values.extend(typing_inspect.get_args(generic_base))

    generic_type_vars = []

    base_generic_bases = typing_inspect.get_generic_bases(controller.__base__)

    type_var_generic_bases = list(
        filter(typing_inspect.is_generic_type, base_generic_bases))

    for type_var_generic_base in type_var_generic_bases:
        generic_type_vars.extend(typing_inspect.get_args(type_var_generic_base))

    return {k: v for k, v in zip(generic_type_vars, generic_values)}


def _update_generic_parameters_signature(generic_dict: Dict, method: Callable):
    """

    Args:
        generic_dict:
        method:

    Returns:

    """
    sig = inspect.signature(method)
    params = sig.parameters

    new_params = []
    has_request:bool=False
    has_response:bool=False
    for k, v in params.items():
        annotation = v.annotation #??????
        if v.name=='request'  :
            has_request = True
        if v.name=="response"  :
            has_response = True
        if typing_inspect.is_typevar(annotation):
            new_params.append(
                inspect.Parameter(name=k, kind=v.kind, annotation=generic_dict[annotation], default=v.default))
        else:
            new_params.append(v)
     
    if not has_request: 
        new_params.append(inspect.Parameter('request', inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Request))
         
    if not has_response: 
        new_params.append(inspect.Parameter('response', inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Response))
         
    
    return_val = generic_dict[sig.return_annotation] if typing_inspect.is_typevar(
        sig.return_annotation) else sig.return_annotation

    setattr(method, "__signature__", sig.replace(parameters=new_params, return_annotation=return_val))


def _update_generic_args(generic_dict: Dict, kwargs) -> Dict:
    """

    Args:
        generic_dict:
        kwargs:

    Returns:

    """
    for k, v in kwargs.items():
        if typing_inspect.is_generic_type(v):
            args = typing_inspect.get_args(v)
            args = [generic_dict[k] if k in generic_dict else k for k in args]
            v.__args__ = args
            kwargs[k] = v

    return kwargs


def _copy_func(f):
    """Based on http://stackoverflow.com/a/6528148/190597 (Glenn Maynard)

    Args:
        f:

    Returns:

    """

    g = types.FunctionType(f.__code__, f.__globals__, name=f.__name__, argdefs=f.__defaults__, closure=f.__closure__)
    g = update_wrapper(g, f)
    g.__kwdefaults__ = f.__kwdefaults__
    return g


def _register_controller_to_router(router: APIRouter, controller: Type[ControllerBase]) -> None:
    """

    Args:
      router: APIRouter:
      controller: ControllerBase:

    Returns:

    """
    path_template = getattr(controller, TEMPLATE_PATH_KEY)
    version = getattr(controller, VER_KEY)

    # Get all the routes information
    routes_dict = _get_routes_in_controller(controller)
    generic_dict = _get_generic_type_var_dict(controller)

    for name, value in routes_dict.items():
        member = getattr(controller, name)
        new_member = _copy_func(member)
        _update_generic_parameters_signature(generic_dict, new_member)
        route_method = getattr(router, value[METHOD_KEY])
        path = _compute_path(value[PATH_KEY], controller.__name__, path_template, version)
        kwargs = _update_generic_args(generic_dict, value[KWARGS_KEY])
        # ????????? fastapi apiroute
        new_route_method = route_method(path, **kwargs)(new_member)
        setattr(controller, name, new_route_method)
    
    cbv(router)(controller)

from fastapi import Request
def _http_method(path: str, method: str, *args, **mwargs):
    def wrapper(func ):
        @wraps(func)
        async def decorator(  *args, **kwargs):
            # ??????????????????????????????????????????
            print(f"start call http metod by decorator:{func.__name__}")
            module = inspect.getmodule(func)
            cls = getattr(module, func.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
            #instance = cls.__dict__.get('__wrapped__', None).__self__ #or cls.__dict__.get('__objclass__', None)(obj)
            response:Response = None
            if 'request' in kwargs and 'response' in kwargs:
                response  = kwargs["response"]
                setattr(cls,'request',kwargs['request'])
                setattr(cls,'response',kwargs['response'])
                await cls._constructor(cls,request = kwargs['request'],response=kwargs['response'])
            if 'request' in kwargs:  
                del kwargs['request']  
            if 'response' in kwargs:  
                del kwargs['response']  
            result:Response = None
            if inspect.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result =  func(*args,**kwargs)
            
            if response:
                result.raw_headers.extend(response.raw_headers)
            await cls._deconstructor(cls,result)
            return result
        setattr(decorator, PATH_KEY, path)
        setattr(decorator, METHOD_KEY, method)
        setattr(decorator, ARGS_KEY, args)
        setattr(decorator, KWARGS_KEY, mwargs)
     
        setattr(decorator, "__signature__", inspect.signature(func))
        return decorator
    return wrapper
